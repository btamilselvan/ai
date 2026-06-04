import { log } from "@/lib/logger";
import { NextRequest, NextResponse } from "next/server";

//function name should be "proxy" for next.js to recognize it as a middleware function
export function proxy(request: NextRequest) {

    // log("debug", "Middleware invoked for request:", { url: request.url, method: request.method, pathname: request.nextUrl.pathname });

    // authentication middleware to check if the user is logged in before allowing access to protected routes
    const protectedRoutes = ["/dashboard", "/dashboard/*"];
    const isProtectedRoute = protectedRoutes.some((route) => request.nextUrl.pathname.startsWith(route));

    if (isProtectedRoute) {
        const authToken = request.cookies.get("authToken")?.value;
        log("debug", "Checking authentication for protected route:", { pathname: request.nextUrl.pathname, authToken });
        //validate auth token. but for now just check if it exists for simplicity. 
        // In a real application, you would want to verify the token's validity and expiration.
        if (!authToken) {
            log("warn", "Unauthorized access attempt to protected route:", { pathname: request.nextUrl.pathname });
            const loginUrl = new URL("/", request.url);
            return NextResponse.redirect(loginUrl);
        }
    }

    return NextResponse.next();
}