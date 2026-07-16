import { getCookie } from '@/lib/cookie'
import { GOOGLE_USER_EMAIL_COOKIE_NAME } from '@/lib/constants'
import { ChatMessage } from "@/lib/models";

export async function chatWithAI(message: ChatMessage) {
    const email = await getCookie(GOOGLE_USER_EMAIL_COOKIE_NAME);
    message.email = email;

    const response = await fetch(`${process.env.API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            "x-api-key": process.env.API_KEY || ""
        },
        body: JSON.stringify( message )
    });
    return await response.json();
}


export async function chatWithManagerAI(message: ChatMessage) {
    const email = await getCookie(GOOGLE_USER_EMAIL_COOKIE_NAME);
    message.email = email;

    const response = await fetch(`${process.env.MANAGER_API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            "x-api-key": process.env.MANAGER_API_KEY || ""
        },
        body: JSON.stringify( message )
    });
    return await response.json();
}