import { NextRequest, NextResponse } from "next/server";
import { log } from "@/lib/logger"
import { ChatMessage } from "@/lib/models";
import { chatWithAI, chatWithManagerAI } from "@/app/services/chat"

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

    log("info", "Slug value is :", { slug: slug[0] });
    const body = await request.json();
    log("info", "Body value is :", { body });
    const message: ChatMessage = body.data;

    if (agent == "calendarai") {
        //call calendar agent
        const aiResponse: ChatMessage = await chatWithAI(message);
        log("info", "AI Response is :", { aiResponse })

        return new Response(JSON.stringify(aiResponse), {
            status: 200,
            headers: { "Content-Type": "application/json" },
        });
    }else if(agent == "pokerai"){
        // call manager agent
        const aiResponse: ChatMessage = await chatWithManagerAI(message);
        log("info", "Manager AI Response is :", { aiResponse })

        return new Response(JSON.stringify(aiResponse), {
            status: 200,
            headers: { "Content-Type": "application/json" },
        });
    }

    const aiMessage: ChatMessage = {
        role: "assistant",
        content: `Hello, you sent me a message: ${message.content}`,
        timestampInUtcMillis: new Date().getUTCMilliseconds(),
        threadId: message.threadId
    }

    return new Response(JSON.stringify(aiMessage), {
        status: 200,
        headers: { "Content-Type": "application/json" },
    });
}

async function invokeCalendarAgent(message: ChatMessage, request: NextRequest) {

}