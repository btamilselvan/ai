export async function saveGoogleCredentials(credentials: any) {
    return await fetch(`${process.env.API_BASE_URL}/google/credentials`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "x-api-key": process.env.API_KEY || ""
        },
        body: credentials
    });
}

export async function getGoogleRefreshToken(email: string) {
    return await fetch(`${process.env.API_BASE_URL}/google/token/refresh?email=${email}`, {
        headers: {
            "x-api-key": process.env.API_KEY || ""
        }
    });
}