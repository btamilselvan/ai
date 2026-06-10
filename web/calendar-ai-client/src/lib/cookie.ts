import { cookies } from "next/headers";

export async function setCookie(name: string, value: string) {
    const cookiesStore = await cookies();
    cookiesStore.set(name, value, {
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        sameSite: "lax",
        path: "/",
        // maxAge: 60 * 60 * 24 * 7, // 7 days
    })
}