export interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    timestampInUtcMillis?: number;
}