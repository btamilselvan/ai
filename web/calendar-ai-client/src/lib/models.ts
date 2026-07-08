export interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    timestampInUtcMillis?: number;
    threadId: string;
    email?: string;
}

export interface ConversationThread {
    id: string;
    label: string;
    createdAt?: number;
    updatedAt?: number;
}
