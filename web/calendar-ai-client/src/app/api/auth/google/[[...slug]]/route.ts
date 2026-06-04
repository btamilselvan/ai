import { NextResponse } from "next/server";
import { log } from "@/lib/logger";
import { cookies } from "next/headers";

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
        return await exchangeCodeForToken(request);
    } else {
        return new NextResponse("Not found", { status: 404 });
    }
}

function initiateGoogleOAuth() {
    // this function will construct the Google OAuth URL with the necessary query parameters and redirect the user to it
    const google_client_id = process.env.GOOGLE_CLIENT_ID;
    const google_redirect_uri = process.env.GOOGLE_REDIRECT_URI;
    const google_auth_scope = process.env.GOOGLE_AUTH_SCOPE;

    const state = Math.random().toString(36).substring(2); // generate a random state parameter for CSRF protection
    // store the state parameter in a cookie or session to verify it later in the callback route
    // for simplicity, we will skip this step in this example, but in a production application, you should implement proper state management for security

    const google_oauth_url = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${google_client_id}&redirect_uri=${google_redirect_uri}&response_type=code&scope=${encodeURIComponent(google_auth_scope)}&state=${state}&access_type=offline`;
    return new NextResponse("Redirecting to Google OAuth...", {
        status: 302,
        headers: {
            Location: google_oauth_url,
        },
    });
}

async function exchangeCodeForToken(request: Request) {
    // this function will exchange the authorization code for an access token by making a POST request to the google oauth API
    const cookiesStore = await cookies();

    // unpack the query parameters from the callback URL
    const { searchParams } = new URL(request.url);
    const code = searchParams.get("code");
    const state = searchParams.get("state");

    //compare state with the value stored in the cookie or session to verify it (skipped in this example for simplicity)

    log("debug", "Extracted code and state from callback URL:", { code, state });

    //exchange the authorization code for an access token by making a POST request to the google oauth API
    const response = await fetch(`https://oauth2.googleapis.com/token`, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
            client_id: process.env.GOOGLE_CLIENT_ID,
            redirect_uri: process.env.GOOGLE_REDIRECT_URI,
            client_secret: process.env.GOOGLE_CLIENT_SECRET,
            grant_type: "authorization_code",
            code: code,
        }),
    });
    log("debug", "Received response from Google token exchange:", { status: response.status });

    if (response.ok) {
        const data = await response.json();
        log("debug", "Received access token from Google:", { data });

        // store the access token in a cookie or session for later use
        cookiesStore.set("googleAccessToken", data.access_token, {
            httpOnly: true,
            secure: process.env.NODE_ENV === "production",
            sameSite: "strict",
            path: "/",
            maxAge: 60 * 60 * 24 * 7, // 7 days
        });

        //obtain refresh token if available and store it as well
        if (data.refresh_token) {
            log("debug", "Received refresh token from Google:", { refresh_token: data.refresh_token });
            cookiesStore.set("googleRefreshToken", data.refresh_token, {
                httpOnly: true,
                secure: process.env.NODE_ENV === "production",
                sameSite: "strict",
                path: "/",
                maxAge: 60 * 60 * 24 * 30, // 30 days
            });
        }
        // store the refresh token in a table in the database associated with the user for later use in refreshing the access token when it expires (skipped in this example for simplicity)
        return NextResponse.redirect(new URL("/dashboard", request.url));
    } else {
        log("error", "Failed to exchange authorization code for access token:", { body: await response.text() });
        return new NextResponse("Failed to authenticate with Google", { status: 500 });
    }
}