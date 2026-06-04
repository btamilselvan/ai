// This file defines the API route for handling user login requests. It receives the email and password from the client, forwards the login request to the backend API, and returns the appropriate response based on the success or failure of the login attempt. 
// The route also includes error handling to manage any issues that may arise during the login process.
// This runs on the server side and is responsible for communicating with the backend API to authenticate the user and manage their session.


import { NextRequest, NextResponse } from "next/server";
import { log } from "@/lib/logger";
import { cookies } from "next/headers"

export async function POST(request: NextRequest, { params }: { params: Promise<{ slug: string[] }> }) {

    const { slug } = await params;
    log("info", "Received request to dynamic route with slug:", { slug })

    try {
        const { email, loginPassword } = await request.json();
        log("debug", "Received login request for email:", { email });
        log("debug", "Using API base URL:", { apiUrl: process.env.API_BASE_URL });

        const response = await fetch(`${process.env.API_BASE_URL}/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                email: email,
                loginPassword: loginPassword,
            }),
        });

        if (!response.ok) {
            log("error", "Login failed with status:", { status: response.status });
            return new NextResponse(JSON.stringify({ message: "Login failed" }), {
                status: response.status,
                headers: { "Content-Type": "application/json" },
            });
        }

        const data = await response.json();
        log("debug", "Login successful, received data:", { data });
        // print authorization header from response
        log("debug", "Authorization header from response:", { authorization: response.headers.get("x-amzn-remapped-authorization") });

        // set the auth token in a cookie for session management
        const cookiesStore = await cookies();
        cookiesStore.set("authToken", response.headers.get("x-amzn-remapped-authorization") || "", {
            httpOnly: true,
            secure: process.env.NODE_ENV === "production",
            sameSite: "strict",
            path: "/",
            maxAge: 60 * 60 * 24 * 7, // 7 days
        });

        return new NextResponse(JSON.stringify(data["data"]), {
            status: 200,
            headers: {
                "Content-Type": "application/json"
            },
        });

    } catch (error) {
        log("error", "Error during login:", { error });
        return new NextResponse(JSON.stringify({ message: "Internal server error" }), {
            status: 500,
            headers: { "Content-Type": "application/json" },
        });
    }
}


//logout
export async function GET(request: NextRequest) {
    // clear the auth token cookie
    const cookiesStore = await cookies();
    cookiesStore.delete("authToken");
    cookiesStore.delete("googleAccessToken");
    cookiesStore.delete("googleRefreshToken");

    return NextResponse.redirect(new URL("/", request.url));
}
