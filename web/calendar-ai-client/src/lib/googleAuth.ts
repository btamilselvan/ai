import { log } from "@/lib/logger"


export function getOauthUrl(state: string) {
    const google_client_id = process.env.GOOGLE_CLIENT_ID;
    const google_redirect_uri = process.env.GOOGLE_REDIRECT_URI;
    const google_auth_scope = process.env.GOOGLE_AUTH_SCOPE;

    const google_oauth_url = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${google_client_id}&redirect_uri=${google_redirect_uri}&response_type=code&scope=${encodeURIComponent(google_auth_scope)}&state=${state}&access_type=offline&prompt=consent`;

    return google_oauth_url;
}

export async function exchangeCodeForToken(code: string) {
    return await fetch(`https://oauth2.googleapis.com/token`, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
            client_id: process.env.GOOGLE_CLIENT_ID!,
            redirect_uri: process.env.GOOGLE_REDIRECT_URI!,
            client_secret: process.env.GOOGLE_CLIENT_SECRET!,
            grant_type: "authorization_code",
            code: code,
        }),
    });
}

export async function getUserInfo(accessToken: string) {
    return await fetch("https://www.googleapis.com/oauth2/v2/userinfo", {
        headers: {
            Authorization: `Bearer ${accessToken}`,
        },
    });
}

export async function isAccessTokenValid(access_token: string) {
    const tokenInfoUri = `https://oauth2.googleapis.com/tokeninfo?access_token=${encodeURIComponent(access_token)}`;
    log("debug", "Validating google access token:", { tokenInfoUri: tokenInfoUri });
    const response = await fetch(tokenInfoUri);
    console.log("response", response.status);
    return response.status == 200;

}

/**
 * Exchange Refresh token for access token
 * @param refresh_token 
 * @returns 
 */
export async function refreshAccessToken(refresh_token: string) {

    const response = await fetch(`https://oauth2.googleapis.com/token`, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
            client_id: process.env.GOOGLE_CLIENT_ID!,
            client_secret: process.env.GOOGLE_CLIENT_SECRET!,
            grant_type: "refresh_token",
            refresh_token: refresh_token,
        }),
    });
    if (response.status == 200) {
        const data = await response.json();
        return data.access_token;
    } else {
        log("error", "Failed to refresh access token", { status: response.status, statusText: response.statusText });
        return null;
    }
}