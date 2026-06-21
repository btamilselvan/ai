import { log } from "@/lib/logger";
import { isAccessTokenValid } from "@/lib/googleAuth";
import { NextRequest, NextResponse } from "next/server";

//function name should be "proxy" for next.js to recognize it as a middleware function
export async function proxy(request: NextRequest) {

    // log("debug", "Middleware invoked for request:", { url: request.url, method: request.method, pathname: request.nextUrl.pathname });

    // authentication middleware to check if the user is logged in before allowing access to protected routes
    const protectedRoutes = ["/dashboard", "/dashboard/*"];
    const isProtectedRoute = protectedRoutes.some((route) => request.nextUrl.pathname.startsWith(route));

    if (isProtectedRoute) {
        const authToken = request.cookies.get("authToken")?.value;
        const googleAccessToken = request.cookies.get("googleAccessToken")?.value;
        log("debug", "Checking authentication for protected route:", { pathname: request.nextUrl.pathname, authToken: authToken, googleAccessToken: googleAccessToken });
        //validate auth token. but for now just check if it exists for simplicity. 
        // In a real application, you would want to verify the token's validity and expiration.
        if (!authToken && !googleAccessToken) {
            log("warn", "Unauthorized access attempt to protected route:", { pathname: request.nextUrl.pathname });
            const loginUrl = new URL("/", request.url);
            return NextResponse.redirect(loginUrl);
        }
        if (googleAccessToken && !await isAccessTokenValid(googleAccessToken)) {
            //redirect to /refresh route
            const refreshUrl = new URL("/api/auth/refresh", request.url);
            //preserve the original url to redirect back to after refreshing the access token
            refreshUrl.searchParams.set("returnTo", request.url);
            return NextResponse.redirect(refreshUrl);
        }
    }
    return NextResponse.next();
}

export const config = {
    // The "matcher" tells Next.js where to apply this middleware
    matcher: '/dashboard/:path*',
};
