import { NextRequest, NextResponse } from "next/server";
import { log } from "@/lib/logger";
import { cookies } from "next/headers";
import { getGoogleRefreshToken } from "@/app/services/auth"
import { refreshAccessToken } from "@/lib/googleAuth";
import { setCookie } from "@/lib/cookie"
import {
    GOOGLE_ACCESS_TOKEN_COOKIE_NAME,
    GOOGLE_USER_EMAIL_COOKIE_NAME,
} from "@/lib/constants"

export async function GET(request: NextRequest) {
    log("debug", "Refreshing access token");

    const cookieStore = await cookies();

    const email = cookieStore.get(GOOGLE_USER_EMAIL_COOKIE_NAME)?.value;
    if (!email) {
        //email cookie not found. cannot refresh token
        //redirect to the login page
        return NextResponse.redirect(new URL("/login", request.url));
    }
    const refreshToken = await getGoogleRefreshToken(email);
    const { searchParams } = new URL(request.url);
    const returnTo = searchParams.get('returnTo') || '/dashboard';

    if (refreshToken.status == 200) {
        const data = await refreshToken.json();
        log("debug", "refresh token response", data);
        const newAccessToken = await refreshAccessToken(data.refresh_token);
        if (newAccessToken) {
            log("debug", "new access token received", { newAccessToken })
            //refresh cookie
            setCookie(GOOGLE_ACCESS_TOKEN_COOKIE_NAME, newAccessToken);
            return NextResponse.redirect(new URL(returnTo, request.url));
        }
    }
    return NextResponse.redirect(new URL("/login", request.url));
}