#!/usr/bin/env python3
"""
Melodio CEO Chat — Lightweight web UI for talking to B from any device.
Proxies messages through the OpenClaw gateway.
"""

import asyncio
import hashlib
import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path

try:
    from aiohttp import web
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--break-system-packages", "aiohttp"])
    from aiohttp import web

# Config
PORT = int(os.getenv("CHAT_PORT", "8888"))
PASSWORD = os.getenv("CHAT_PASSWORD", "melodio2026")
AGENT = os.getenv("CHAT_AGENT", "dorin-ceo")
TOKEN_SECRET = secrets.token_hex(32)

# Session tokens (in-memory)
valid_tokens = set()

def hash_token(t):
    return hashlib.sha256(t.encode()).hexdigest()

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Melodio CEO Chat</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #0a0a0f; color: #e5e7eb; font-family: 'Inter', system-ui, sans-serif; height: 100vh; display: flex; flex-direction: column; }
.header { padding: 16px 20px; border-bottom: 1px solid #1f1f2e; display: flex; align-items: center; gap: 12px; }
.header h1 { font-size: 20px; font-weight: 800; background: linear-gradient(135deg, #fff, #c4b5fd, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.header .badge { font-size: 11px; background: rgba(139,92,246,0.15); color: #a78bfa; padding: 3px 10px; border-radius: 20px; border: 1px solid rgba(139,92,246,0.3); }
.messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 12px; }
.msg { max-width: 80%; padding: 12px 16px; border-radius: 16px; font-size: 14px; line-height: 1.5; white-space: pre-wrap; word-wrap: break-word; }
.msg.user { align-self: flex-end; background: #8b5cf6; color: white; border-bottom-right-radius: 4px; }
.msg.bot { align-self: flex-start; background: #1a1a2e; color: #e5e7eb; border-bottom-left-radius: 4px; border: 1px solid #2a2a3a; }
.msg.bot .name { font-size: 11px; color: #a78bfa; font-weight: 600; margin-bottom: 4px; }
.msg.system { align-self: center; font-size: 12px; color: #6b7280; }
.typing { align-self: flex-start; padding: 12px 16px; font-size: 13px; color: #6b7280; }
.input-area { padding: 16px 20px; border-top: 1px solid #1f1f2e; display: flex; gap: 10px; }
.input-area input { flex: 1; background: #13131a; border: 1px solid #2a2a3a; border-radius: 12px; padding: 12px 16px; color: #f9fafb; font-size: 14px; outline: none; }
.input-area input:focus { border-color: #8b5cf6; box-shadow: 0 0 0 2px rgba(139,92,246,0.2); }
.input-area button { background: #8b5cf6; color: white; border: none; border-radius: 12px; padding: 12px 20px; font-weight: 600; cursor: pointer; font-size: 14px; }
.input-area button:hover { background: #7c3aed; }
.input-area button:disabled { opacity: 0.5; cursor: not-allowed; }
.login { height: 100vh; display: flex; align-items: center; justify-content: center; }
.login-box { background: #13131a; border: 1px solid #2a2a3a; border-radius: 20px; padding: 40px; width: 340px; text-align: center; }
.login-box h2 { font-size: 28px; font-weight: 800; background: linear-gradient(135deg, #fff, #c4b5fd); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 8px; }
.login-box p { font-size: 13px; color: #6b7280; margin-bottom: 24px; }
.login-box input { width: 100%; background: #0a0a0f; border: 1px solid #2a2a3a; border-radius: 10px; padding: 12px; color: #f9fafb; font-size: 14px; outline: none; margin-bottom: 12px; }
.login-box button { width: 100%; background: #8b5cf6; color: white; border: none; border-radius: 10px; padding: 12px; font-weight: 600; cursor: pointer; font-size: 14px; }
.login-box .error { color: #f87171; font-size: 12px; margin-top: 8px; }
</style>
</head>
<body>
<div id="app"></div>
<script>
const app = document.getElementById('app');
let token = localStorage.getItem('chat_token') || '';

function renderLogin(err) {
  app.innerHTML = `
    <div class="login"><div class="login-box">
      <h2>Melodio</h2>
      <p>CEO Command Interface</p>
      <input type="password" id="pw" placeholder="Password" onkeydown="if(event.key==='Enter')doLogin()">
      <button onclick="doLogin()">Enter</button>
      ${err ? '<div class="error">'+err+'</div>' : ''}
    </div></div>`;
  document.getElementById('pw')?.focus();
}

async function doLogin() {
  const pw = document.getElementById('pw').value;
  const res = await fetch('/api/login', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({password:pw})});
  const data = await res.json();
  if (data.token) { token = data.token; localStorage.setItem('chat_token', token); renderChat(); }
  else renderLogin(data.error || 'Wrong password');
}

function renderChat() {
  app.innerHTML = `
    <div class="header"><h1>Melodio</h1><span class="badge">B — AI CEO</span></div>
    <div class="messages" id="msgs"><div class="msg system">Connected. Type a message to talk to B.</div></div>
    <div class="input-area">
      <input id="input" placeholder="Message B..." onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();sendMsg()}">
      <button id="sendbtn" onclick="sendMsg()">Send</button>
    </div>`;
  document.getElementById('input')?.focus();
}

async function sendMsg() {
  const input = document.getElementById('input');
  const text = input.value.trim();
  if (!text) return;
  input.value = '';
  addMsg(text, 'user');
  document.getElementById('sendbtn').disabled = true;
  addTyping();
  try {
    const res = await fetch('/api/chat', {method:'POST', headers:{'Content-Type':'application/json','Authorization':'Bearer '+token}, body:JSON.stringify({message:text})});
    removeTyping();
    if (res.status === 401) { localStorage.removeItem('chat_token'); renderLogin('Session expired'); return; }
    const data = await res.json();
    addMsg(data.reply || data.error || 'No response', 'bot');
  } catch(e) { removeTyping(); addMsg('Connection error: '+e.message, 'system'); }
  document.getElementById('sendbtn').disabled = false;
  document.getElementById('input')?.focus();
}

function addMsg(text, type) {
  const msgs = document.getElementById('msgs');
  const div = document.createElement('div');
  div.className = 'msg ' + type;
  if (type === 'bot') div.innerHTML = '<div class="name">B ⚡</div>' + escHtml(text);
  else div.textContent = text;
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}

function addTyping() { const d = document.createElement('div'); d.className='typing'; d.id='typing'; d.textContent='B is thinking...'; document.getElementById('msgs').appendChild(d); }
function removeTyping() { document.getElementById('typing')?.remove(); }
function escHtml(t) { const d=document.createElement('div'); d.textContent=t; return d.innerHTML; }

// Init
if (token) { fetch('/api/verify', {headers:{'Authorization':'Bearer '+token}}).then(r => r.ok ? renderChat() : renderLogin()).catch(() => renderLogin()); }
else renderLogin();
</script>
</body>
</html>"""

async def handle_login(request):
    data = await request.json()
    if data.get("password") == PASSWORD:
        tok = secrets.token_urlsafe(32)
        valid_tokens.add(hash_token(tok))
        return web.json_response({"token": tok})
    return web.json_response({"error": "Wrong password"}, status=401)

async def handle_verify(request):
    tok = request.headers.get("Authorization", "").replace("Bearer ", "")
    if hash_token(tok) in valid_tokens:
        return web.json_response({"ok": True})
    return web.json_response({"error": "invalid"}, status=401)

async def handle_chat(request):
    tok = request.headers.get("Authorization", "").replace("Bearer ", "")
    if hash_token(tok) not in valid_tokens:
        return web.json_response({"error": "Unauthorized"}, status=401)

    data = await request.json()
    message = data.get("message", "").strip()
    if not message:
        return web.json_response({"error": "Empty message"})

    try:
        proc = await asyncio.create_subprocess_exec(
            "openclaw", "send", "--agent", AGENT, "--text", message, "--wait", "120",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=130)
        reply = stdout.decode().strip()
        if not reply:
            reply = stderr.decode().strip() or "No response received."
        return web.json_response({"reply": reply})
    except asyncio.TimeoutError:
        return web.json_response({"reply": "Response timed out. B might be busy with a long task."})
    except Exception as e:
        return web.json_response({"error": str(e)})

async def handle_index(request):
    return web.Response(text=HTML_PAGE, content_type="text/html")

app = web.Application()
app.router.add_get("/", handle_index)
app.router.add_post("/api/login", handle_login)
app.router.add_get("/api/verify", handle_verify)
app.router.add_post("/api/chat", handle_chat)

if __name__ == "__main__":
    print(f"\n⚡ Melodio CEO Chat")
    print(f"   URL: http://0.0.0.0:{PORT}")
    print(f"   Password: {PASSWORD}")
    print(f"   Agent: {AGENT}\n")
    web.run_app(app, host="0.0.0.0", port=PORT, print=None)
