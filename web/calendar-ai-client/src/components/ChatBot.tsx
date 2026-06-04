"use client"

import { useState } from "react"
import { ChatMessage } from "@/lib/models";

interface ChatBotProps {
    initialMessages?: ChatMessage[];
    sendFunc: (message: ChatMessage) => Promise<ChatMessage>;
}

export default function ChatBot({ initialMessages, sendFunc }: ChatBotProps) {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState("");

    const sendMessage = () => {
        if (!input.trim()) return;
        const userMessage: ChatMessage = { role: "user", content: input, timestampInUtcMillis: new Date().getUTCMilliseconds() }
        setMessages((prev) => [...prev, { role: "user", content: input }]);
        sendFunc(userMessage).then((response) => {
            setMessages((prev) => [...prev, response]);
        });

        setInput("");
    };

    return (
        <div className="flex flex-col h-full border rounded-lg overflow-hidden">
            <div className="flex-1 overflow-y-auto p-4 space-y-2 bg-white">
                {messages.length === 0 && (
                    <p className="text-gray-400 text-sm text-center">No messages yet. Start the conversation!</p>
                )}
                {messages.map((msg, i) => (
                    <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                        <div className={`max-w-xs px-4 py-2 rounded-lg text-sm ${msg.role === "user" ? "bg-blue-500 text-white" : "bg-gray-200 text-gray-800"}`}>
                            {msg.content}
                        </div>
                    </div>
                ))}
            </div>
            <div className="flex items-center gap-2 p-3 border-t bg-gray-50">
                <input
                    type="text"
                    className="flex-1 border rounded p-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
                    placeholder="Type a message..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                />
                <button
                    onClick={sendMessage}
                    className="bg-blue-500 text-white px-4 py-2 rounded text-sm hover:bg-blue-600"
                >
                    Send
                </button>
            </div>
        </div>
    );
}
