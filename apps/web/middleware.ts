import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PROTECTED_PATHS = [
  "/dashboard",
  "/settings",
  "/fan/dashboard",
  "/ambassador",
  "/transactions",
];

export function middleware(request: NextRequest) {
  const token = request.cookies.get("melodio_token")?.value;
  const { pathname } = request.nextUrl;

  const isProtected = PROTECTED_PATHS.some((p) => pathname.startsWith(p));

  if (isProtected && !token) {
    const loginUrl = new URL("/auth/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/settings/:path*",
    "/fan/dashboard/:path*",
    "/ambassador/:path*",
    "/transactions/:path*",
  ],
};
