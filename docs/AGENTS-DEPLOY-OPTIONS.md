# Agents Service — Deployment Options
**Context:** Railway Free plan limit is 4 services (already at capacity). The `apps/agents`
service (23 AI agents, LangGraph + Anthropic Claude) needs a home.

---

## Current Status
- Agents code: ✅ Built and ready at `apps/agents/`
- Railway: ❌ 4-service limit hit — cannot add 5th service on Free plan
- Local run: ⚠️ Requires Python deps (anthropic, langgraph, etc.) — install once then works

---

## Option A — Upgrade Railway to Hobby Plan

**Cost:** $20/month + usage-based compute (~$5–15/mo for agents)
**Estimated total:** ~$25–35/month

### Steps
1. Railway dashboard → Settings → Upgrade to Hobby
2. Add new service from `apps/agents/` directory
3. Set env vars (copy from `.env`)
4. Deploy

### Pros
- ✅ Everything in one place (Railway) — simple operations
- ✅ Auto-deploy on git push
- ✅ Managed HTTPS, health checks, restarts
- ✅ Same infrastructure as API + Web services
- ✅ Scales automatically under load

### Cons
- ❌ $20+/mo base cost (on top of existing Railway bill)
- ❌ Agents are mostly idle (cold AI calls) — paying for compute you may not use

---

## Option B — Free Tier on Fly.io or Render

**Cost:** $0 (within free tier limits)

### Fly.io
- Free: 3 shared-CPU VMs, 256 MB RAM each
- Deploy: `fly launch` from `apps/agents/`
- Limitation: 256 MB RAM may be tight for LangGraph + Anthropic SDK

### Render
- Free: 512 MB RAM, sleeps after 15 min inactivity (cold starts ~30 sec)
- Deploy: Connect GitHub, select `apps/agents/`, set build/start commands

### Steps (Fly.io example)
```bash
cd ~/projects/echo/apps/agents
fly auth login
fly launch --name melodio-agents --region sjc
fly secrets set ANTHROPIC_API_KEY=... DATABASE_URL=...
fly deploy
```

### Pros
- ✅ Free — no additional monthly cost
- ✅ Still cloud-hosted, auto-HTTPS

### Cons
- ❌ Render free tier sleeps (cold starts kill real-time agent responsiveness)
- ❌ Fly.io 256 MB RAM limit may cause OOM with multiple agents
- ❌ Separate platform = more ops complexity
- ❌ Free tiers have usage caps — if agents get busy, you'll hit limits

---

## Option C — Mac Mini as Persistent Background Service (launchd)

**Cost:** $0 (already running 24/7)

Run the agents service directly on the Mac mini using a macOS `launchd` plist.
This keeps the agents alive permanently, restarts on crash, and logs to file.

### Setup

**1. Create the plist file:**
```bash
cat > ~/Library/LaunchAgents/io.melodio.agents.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>io.melodio.agents</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/bm-007/projects/echo/apps/agents/main.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/bm-007/projects/echo/apps/agents</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>ANTHROPIC_API_KEY</key>
        <string>sk-ant-api03-...</string>
        <key>DATABASE_URL</key>
        <string>postgresql+asyncpg://...</string>
        <key>REDIS_URL</key>
        <string>redis://localhost:6379</string>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/bm-007/projects/echo/logs/agents.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/bm-007/projects/echo/logs/agents-error.log</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>ThrottleInterval</key>
    <integer>10</integer>
</dict>
</plist>
EOF
```

**2. Load and start:**
```bash
mkdir -p ~/projects/echo/logs
launchctl load ~/Library/LaunchAgents/io.melodio.agents.plist
launchctl start io.melodio.agents
```

**3. Check status:**
```bash
launchctl list | grep melodio
tail -f ~/projects/echo/logs/agents.log
```

**4. Manage:**
```bash
# Stop:    launchctl stop io.melodio.agents
# Restart: launchctl kickstart -k gui/$(id -u)/io.melodio.agents
# Remove:  launchctl unload ~/Library/LaunchAgents/io.melodio.agents.plist
```

### Pros
- ✅ **$0 cost** — Mac mini already running 24/7
- ✅ Full RAM and CPU available (Mac mini M2 has 8–16 GB)
- ✅ No cold starts — agents always warm
- ✅ Automatic restart on crash (KeepAlive=true)
- ✅ Logs stored locally
- ✅ Direct access to local Redis and DB if needed
- ✅ No deployment pipeline needed for agents iteration

### Cons
- ❌ Agents not accessible from the internet directly (need to expose via API tunnel or ngrok if needed)
- ❌ Single point of failure = if Mac mini goes offline, agents go offline
- ❌ Not auto-deployed on git push (manual restart needed after code changes)

---

## ⭐ Recommendation: Option C (Mac mini launchd)

**Rationale:**
1. **Agents are backend workers** — they don't serve HTTP directly. They process jobs dispatched by the Railway API. The API can call agents over the internal network or message bus (Redis pub/sub), so internet-reachability isn't required.
2. **Mac mini is already running 24/7** — zero additional cost.
3. **M2 Mac mini has plenty of RAM** — 23 LangGraph agents run comfortably.
4. **Option A costs real money** ($25+/mo) for a service that mostly idles waiting for work.
5. **Option B free tiers** are too constrained (RAM, sleep behavior) for production AI agents.

**When to revisit:** If the business starts scaling and agents handle 100+ concurrent jobs/day, Option A (Railway Hobby) becomes worth it for the operational simplicity.

---

## Next Steps for Option C
1. Install deps once: `pip3 install -r ~/projects/echo/apps/agents/requirements.txt --break-system-packages`
2. Copy the plist above with real env vars from `.env`
3. Run `launchctl load ...` to start
4. Confirm agents are processing: `tail -f ~/projects/echo/logs/agents.log`

---

*Generated by B (AI CEO) — March 2026*
