import { log } from "@/lib/logger";
import { isAccessTokenValid, refreshAccessToken } from "@/lib/googleAuth";
import { NextRequest, NextResponse } from "next/server";
import { getGoogleRefreshToken } from "@/app/services/auth"
import { setCookie } from "@/lib/cookie"
import {
    GOOGLE_ACCESS_TOKEN_COOKIE_NAME,
    GOOGLE_USER_EMAIL_COOKIE_NAME,
} from "@/lib/constants"

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
        if ((!authToken && !googleAccessToken) || (googleAccessToken && !await validateAndRenewGoogleAccessToken(googleAccessToken, request))) {
            log("warn", "Unauthorized access attempt to protected route:", { pathname: request.nextUrl.pathname });
            const loginUrl = new URL("/", request.url);

            return NextResponse.redirect(loginUrl);
        }
    }

    return NextResponse.next();
}

async function validateAndRenewGoogleAccessToken(googleAccessToken: string, request: NextRequest) {
    const isValid = await isAccessTokenValid(googleAccessToken);

    if (isValid) {
        // token valid
        return true;
    }
    const email = request.cookies.get(GOOGLE_USER_EMAIL_COOKIE_NAME)?.value;
    if (!email) {
        //email cookie not found. cannot refresh token
        return false;
    }
    const refreshToken = await getGoogleRefreshToken(email);
    if (refreshToken.status == 200) {
        const data = await refreshToken.json();
        log("debug", "refresh token response", data);
        const newAccessToken = await refreshAccessToken(data.get("refresh_token"));
        if (newAccessToken) {
            //refresh cookie
            setCookie(GOOGLE_ACCESS_TOKEN_COOKIE_NAME, newAccessToken);
            return true;
        }
    }
    return false;
}
