import { NextResponse } from "next/server";
import { log } from "@/lib/logger";
import { exchangeCodeForToken, getOauthUrl, getUserInfo } from "@/lib/googleAuth"
import { saveGoogleCredentials } from "@/app/services/auth"
import { setCookie } from "@/lib/cookie"
import * as Constants from "@/lib/constants"

interface RouteParams {
    params: Promise<{
        slug?: string[]
    }>
}

// next.js will pass context parameter to this function when the user accesses the /api/auth/google/[...slug] route, and we can use the slug parameter to determine which action to take (e.g., initiate login or handle callback)
export async function GET(request: Request, context: RouteParams) {
    // this function will be called when the user clicks the "Sign in with Google" button in the LoginForm component, and it will redirect the user to the Google OAuth flow
    // after the user successfully authenticates with Google, they will be redirected back to the client application with an authorization code that can be exchanged for an access token to authenticate the user in the application

    const { slug } = await context.params;

    log("debug", "Received request to Google auth route with slug:", { slug });

    // if no slug is provided, return 404 response
    if (!slug || slug.length === 0) {
        return new NextResponse("Not found", { status: 404 });
    }
    // if slug is provided, check the action and handle accordingly
    const action = slug[0];
    if (action === "login") {
        return initiateGoogleOAuth();
    } else if (action === "callback") {
        return await getToken(request);
    } else {
        return new NextResponse("Not found", { status: 404 });
    }
}

function initiateGoogleOAuth() {
    // this function will construct the Google OAuth URL with the necessary query parameters and redirect the user to it
    const state = Math.random().toString(36).substring(2); // generate a random state parameter for CSRF protection
    // store the state parameter in a cookie or session to verify it later in the callback route
    // for simplicity, we will skip this step in this example, but in a production application, you should implement proper state management for security

    const google_oauth_url = getOauthUrl(state);
    return new NextResponse("Redirecting to Google OAuth...", {
        status: 302,
        headers: {
            Location: google_oauth_url,
        },
    });
}

async function getToken(request: Request) {
    // this function will exchange the authorization code for an access token by making a POST request to the google oauth API

    // unpack the query parameters from the callback URL
    const { searchParams } = new URL(request.url);
    const code = searchParams.get("code");
    const state = searchParams.get("state");
    //compare state with the value stored in the cookie or session to verify it (skipped in this example for simplicity)

    if (!code) {
        const loginUrl = new URL("/", request.url);
        return NextResponse.redirect(loginUrl);
    }

    log("debug", "Extracted code and state from callback URL:", { code, state });

    //exchange the authorization code for an access token by making a POST request to the google oauth API
    const response = await exchangeCodeForToken(code);
    log("debug", "Received response from Google token exchange:", { status: response.status });

    if (response.ok) {
        const data = await response.json();
        log("debug", "Received access token from Google:", { data });

        // store the access token in a cookie or session for later use
        await setCookie(Constants.GOOGLE_ACCESS_TOKEN_COOKIE_NAME, data.access_token);

        // fetch user info
        const userResponse = await getUserInfo(data.access_token);
        const userData = await userResponse.json();
        //assume userResponse is OK. store user email in cookie
        await setCookie(Constants.GOOGLE_USER_EMAIL_COOKIE_NAME, userData.email);
        await setCookie(Constants.GOOGLE_USERNAME_COOKIE_NAME, userData.name);

        log("debug", "Received user info from Google:", { userData });

        //post google auth credentials to the backend
        const apiResponse = await saveGoogleCredentials(JSON.stringify({
            access_token: data.access_token,
            refresh_token: data.refresh_token,
            scope: data.scope,
            user_id: userData.id,
            email: userData.email,
            name: userData.name,
            picture: userData.picture
        }));
        log("info", "google credentials sent to the backend server", { "status": await apiResponse.json() });

        return NextResponse.redirect(new URL("/dashboard", request.url));
    } else {
        log("error", "Failed to exchange authorization code for access token:", { body: await response.text() });
        return new NextResponse("Failed to authenticate with Google", { status: 500 });
    }
}