"use client"

import { useState } from "react"
import { ChatMessage, ConversationThread } from "@/lib/models";

interface ChatBotProps {
    // initialMessages?: ChatMessage[];
    readonly sendFunc: (message: ChatMessage) => Promise<ChatMessage>;
    // readonly currentConversationId?: string;
    readonly availableConversations: ConversationThread[]
}

export default function ChatBot({ sendFunc, availableConversations }: ChatBotProps) {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState("");
    const [drawerOpen, setDrawerOpen] = useState(false);
    const [activeThread, setActiveThread] = useState<string>("");
    // const [currentConversationId, setCurrentConversationId] = 

    const sendMessage = () => {
        if (!input.trim()) return;
        const userMessage: ChatMessage = { role: "user", content: input, threadId: activeThread }
        setMessages((prev) => [...prev, userMessage]);
        sendFunc(userMessage).then((response) => {
            setMessages((prev) => [...prev, response]);
        });
        setInput("");
    };

    const startNew = () => {
        setMessages([]);
        setActiveThread("");
        setDrawerOpen(false);
        setActiveThread(Date.now().toString());
    };

    return (
        <div className="flex h-full border rounded-lg overflow-hidden">

            {/* Drawer */}
            <div className={`flex flex-col bg-gray-50 border-r transition-all duration-200 overflow-hidden ${
                drawerOpen ? "w-64" : "w-0"
            }`}>
                <div className="flex items-center justify-between p-3 border-b">
                    <span className="text-sm font-semibold text-gray-700">Conversations</span>
                    <button onClick={() => setDrawerOpen(false)} className="text-gray-400 hover:text-gray-600" title="Close">
                        <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>
                <ul className="flex-1 overflow-y-auto p-2 space-y-1">
                    {availableConversations.map((t) => (
                        <li key={t.id}>
                            <button
                                onClick={() => { setActiveThread(t.id); setDrawerOpen(false); }}
                                className={`w-full text-left px-3 py-2 rounded text-sm hover:bg-gray-200 ${
                                    activeThread === t.id ? "bg-gray-200 font-medium" : "text-gray-700"
                                }`}
                            >
                                {t.label}
                            </button>
                        </li>
                    ))}
                </ul>
            </div>

            {/* Main chat */}
            <div className="flex flex-col flex-1 min-w-0">
                <div className="flex items-center gap-2 p-3 border-b">
                    {/* Toggle drawer */}
                    <button onClick={() => setDrawerOpen((o) => !o)} className="text-gray-500 hover:text-gray-800" title="Conversations">
                        <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                        </svg>
                    </button>
                    
                    {/* New conversation */}
                    <button onClick={startNew} className="text-gray-500 hover:text-gray-800" title="New conversation">
                        <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
                        </svg>
                    </button>
                </div>

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
        </div>
    );
}
