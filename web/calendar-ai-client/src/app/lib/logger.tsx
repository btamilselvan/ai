// This file contains a simple logging utility that can be used to log messages with different levels (info, warn, error) along with a timestamp and any additional metadata. 
// The logs are only printed on the server side to avoid cluttering the client-side console.

type LogLevel = "info" | "warn" | "error" | "debug";

export function log(level: LogLevel, message: string, meta: Record<string, any> = {}) {
    const timestamp = new Date().toISOString();
    const logEntry = {
        timestamp,
        level,
        message,
        ...meta,
    };

    // log only on the server side
    if (!globalThis.window) {
        console.log(JSON.stringify(logEntry));
    }
}