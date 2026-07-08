"use client"

import { useState } from "react"
import ChatBot from "@/components/ChatBot"
import { ChatMessage, ConversationThread } from "@/lib/models";

interface ChatBotProps {
    threads?: string[]
    currentThreadId?: string
}

export default function RecipeAIBot() {

    // load available conversations for the user - TODO
    const availableConversations = [{ id: "thread1", label: "Calendar Help" },
    { id: "thread2", label: "Event Creation" },
    { id: "thread3", label: "Meeting Scheduling" },]

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
            <ChatBot sendFunc={chatWithAI} availableConversations={availableConversations} />
        </div>
    )
}