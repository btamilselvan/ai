import { NextRequest, NextResponse } from "next/server";
import { log } from "@/lib/logger"
import { ChatMessage } from "@/lib/models";

// next js context object properties (for now it contains only params. maybe nextjs will add more properties in the future!)
interface ContextParamProps {
    params: Promise<{ slug: string[] }>
}

export async function POST(request: NextRequest, context: ContextParamProps) {

    // dynamically unpack context and fetch just 'params' -> {params} : {params: Promise<{ slug: string[] }> }

    const params = await context.params;
    const slug: string[] = params.slug;

    if (!slug || slug.length === 0) {
        return new NextResponse(JSON.stringify({ error: "Invalid Slug" }), {
            status: 400,
            headers: { "Content-Type": "application/json" },
        });
    }

    const agent = slug[0]

    if (agent == "calendarai") {
        //call calendar agent
    }

    log("info", "Slug value is :", { slug: slug[0] });
    const body = await request.json();
    log("info", "Body value is :", { body });
    const message: ChatMessage = body.data;

    const aiMessage: ChatMessage = {
        role: "assistant",
        content: `Hello, you sent me a message: ${message.content}`,
        timestampInUtcMillis: new Date().getUTCMilliseconds(),
    }

    return new Response(JSON.stringify(aiMessage), {
        status: 200,
        headers: { "Content-Type": "application/json" },
    });
}

async function invokeCalendarAgent(message: ChatMessage){

}