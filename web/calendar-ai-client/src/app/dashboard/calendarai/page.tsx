"use client"

import { useState } from "react"
import ChatBot from "@/components/ChatBot"
import { ChatMessage } from "@/lib/models";

export default function RecipeAIBot() {

    const chatWithAI = async (message: ChatMessage) => {
        //return a promise of ChatMessage
        // const chatMessage: ChatMessage = { role: "assistant", content: "Hello! How can I help you today?" }

        const aiResponse = await fetch("/api/chat/calendarai",
            {
                method: "POST",
                body: JSON.stringify({ data: message }),
                headers: {
                    "Content-Type": "application/json"
                }
            });

        return aiResponse.json();
    }

    return (
        <div>
            <h1>Calendar AI Bot</h1>
            <ChatBot sendFunc={chatWithAI} />
        </div>
    )
}