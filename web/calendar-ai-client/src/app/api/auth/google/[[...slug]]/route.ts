import { NextResponse } from "next/server";
import { log } from "@/app/lib/logger";

interface RouteParams {
    params: Promise<{
        slug?: string[]
    }>
}

// next.js will pass context parameter to this function when the user accesses the /api/auth/google/[...slug] route, and we can use the slug parameter to determine which action to take (e.g., initiate login or handle callback)
export async function GET(request: Request, context: RouteParams) {
    // this function will be called when the user clicks the "Sign in with Google" button in the LoginForm component, and it will redirect the user to the Google OAuth flow
    // after the user successfully authenticates with Google, they will be redirected back to the client application with an authorization code that can be exchanged for an access token to authenticate the user in the application

    const google_client_id = process.env.GOOGLE_CLIENT_ID;
    const google_redirect_uri = process.env.GOOGLE_REDIRECT_URI;
    const google_auth_scope = process.env.GOOGLE_AUTH_SCOPE;

    const { slug } = await context.params;

    log("debug", "Received request to Google auth route with slug:", { slug });

    // if no slug is provided, return 404 response
    if (!slug || slug.length === 0) {
        return new NextResponse("Not found", { status: 404 });
    }
    // if slug is provided, check the action and handle accordingly
    const action = slug[0];
    if (action === "login") {
        // initiate the Google OAuth flow by redirecting the user to the appropriate URL
        const state = Math.random().toString(36).substring(2); // generate a random state parameter for CSRF protection
        // store the state parameter in a cookie or session to verify it later in the callback route
        // for simplicity, we will skip this step in this example, but in a production application, you should implement proper state management for security

        // construct the Google OAuth URL with the necessary query parameters
        const google_oauth_url = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${google_client_id}&redirect_uri=${google_redirect_uri}&response_type=code&scope=${encodeURIComponent(google_auth_scope)}&state=${state}&access_type=offline&prompt=consent`;

        return new NextResponse("Redirecting to Google OAuth...", {
            status: 302,
            headers: {
                Location: google_oauth_url,
            },
        });
    } else if (action === "callback") {
        log("debug", "Received Google OAuth callback with slug:", { slug });
        // unpack the query parameters from the callback URL
        const { searchParams } = new URL(request.url);
        const code = searchParams.get("code");
        const state = searchParams.get("state");
        log("debug", "Extracted code and state from callback URL:", { code, state });

        return NextResponse.redirect(new URL("/dashboard", request.url));
    } else {
        return new NextResponse("Not found", { status: 404 });
    }
}