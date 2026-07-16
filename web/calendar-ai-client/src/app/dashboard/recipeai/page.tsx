"use client"

import { useState } from "react"
import ChatBot from "@/components/ChatBot"
import { ChatMessage } from "@/lib/models";

export default function RecipeAIBot() {

    const chatWithAI = (message: ChatMessage) => {
        //return a promise of ChatMessage
        const chatMessage: ChatMessage = { role: "assistant", content: "Hello! How can I help you today?", "threadId": "t111" }
        return Promise.resolve(chatMessage);
    }

    return (

        <div className="flex flex-col h-full">
            <h1 className="mb-2">Recipe AI Bot</h1>
            <div className="flex-1 min-h-0">
                <ChatBot sendFunc={chatWithAI} availableConversations={[{ id: "thread1", label: "Recipe Help" },
                { id: "thread2", label: "Dish Suggestions" },
                { id: "thread3", label: "Cooking Tips" },]} />
            </div>
        </div>
    )
}