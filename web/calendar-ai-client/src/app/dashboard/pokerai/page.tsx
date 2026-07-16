"use client"

import { useState } from "react"
import ChatBot from "@/components/ChatBot"
import { ChatMessage } from "@/lib/models";

export default function RecipeAIBot() {

    // load available conversations for the user - TODO
    const availableConversations = [{ id: "thread1", label: "Calendar Help" },
    { id: "thread2", label: "Event Creation" },
    { id: "thread3", label: "Meeting Scheduling" },]

    const chatWithAI = async (message: ChatMessage) => {
        //return a promise of ChatMessage
        console.log("Sending message to manager AI: ", message);
        const aiResponse = await fetch("/api/chat/pokerai",
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

        <div className="flex flex-col h-full">
            <h1 className="mb-2">Poker AI Bot</h1>
            <div className="flex-1 min-h-0">
                <ChatBot sendFunc={chatWithAI} availableConversations={availableConversations} />
            </div>
        </div>
    )
}