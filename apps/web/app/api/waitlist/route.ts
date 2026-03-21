import { NextRequest, NextResponse } from "next/server";
import { promises as fs } from "fs";
import path from "path";

const WAITLIST_FILE = path.join(process.cwd(), "waitlist.json");

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const email = (body.email ?? "").trim().toLowerCase();

    if (!email || !email.includes("@") || !email.includes(".")) {
      return NextResponse.json({ success: false, message: "Invalid email." }, { status: 400 });
    }

    // Load or initialise list
    let list: { email: string; joinedAt: string }[] = [];
    try {
      const raw = await fs.readFile(WAITLIST_FILE, "utf-8");
      list = JSON.parse(raw);
    } catch {
      // file doesn't exist yet — start fresh
    }

    // Deduplicate
    if (list.some((entry) => entry.email === email)) {
      return NextResponse.json({ success: true, message: "You are already on the list." });
    }

    list.push({ email, joinedAt: new Date().toISOString() });
    await fs.writeFile(WAITLIST_FILE, JSON.stringify(list, null, 2), "utf-8");

    return NextResponse.json({ success: true, message: "You are on the list." });
  } catch (err) {
    console.error("[waitlist]", err);
    return NextResponse.json({ success: false, message: "Server error." }, { status: 500 });
  }
}
