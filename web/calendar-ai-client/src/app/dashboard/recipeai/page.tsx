"use client"

import { useState } from "react"
import ChatBot from "@/components/ChatBot"
import { ChatMessage } from "@/lib/models";

export default function RecipeAIBot() {

    const chatWithAI = (message: ChatMessage) => {
        //return a promise of ChatMessage
        const chatMessage: ChatMessage = { role: "assistant", content: "Hello! How can I help you today?" }
        return Promise.resolve(chatMessage);
    }

    return (
        <div>
            <h1>Recipe AI Bot</h1>
            <ChatBot sendFunc={chatWithAI} />
        </div>
    )
}