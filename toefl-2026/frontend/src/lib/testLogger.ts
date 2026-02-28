import { API_BASE_URL } from "./api-config";
import { useTestStore } from "../store/testStore";

export interface LogEvent {
    event_type: string;
    question_id?: string;
    event_data?: any;
    event_timestamp: string;
}

class TestLogger {
    private buffer: LogEvent[] = [];
    private flashInterval: NodeJS.Timeout | null = null;
    private browserFingerprint: string | null = null;

    constructor() {
        if (typeof window !== "undefined") {
            // Rough browser fingerprinting purely for ETS log analytics mimicry
            this.browserFingerprint = navigator.userAgent + "|" + (navigator.language || '');

            // Set up interval to flush logs every 5 seconds (to avoid hitting API too often)
            this.flashInterval = setInterval(() => {
                this.flush();
            }, 5000);

            // Also flush when user tries to close page
            window.addEventListener("beforeunload", () => {
                this.flush();
            });

            // Log blur/focus for anti-cheat
            window.addEventListener("blur", () => {
                this.logEvent("BROWSER_BLUR");
            });
            window.addEventListener("focus", () => {
                this.logEvent("BROWSER_FOCUS");
            });
        }
    }

    public logEvent(eventType: string, questionId?: string, data?: any) {
        this.buffer.push({
            event_type: eventType,
            question_id: questionId,
            event_data: data,
            event_timestamp: new Date().toISOString()
        });

        // Hard flush if buffer gets too large (e.g. 50 events)
        if (this.buffer.length >= 50) {
            this.flush();
        }
    }

    public async flush() {
        if (this.buffer.length === 0) return;

        // Take a snapshot
        const logsToSend = [...this.buffer];
        this.buffer = []; // Clear current buffer to avoid double submission

        // Get student/session info
        const state = useTestStore.getState();
        const sessionId = state.sessionId;
        const studentId = state.studentId;

        // If no active session, we can't save them. Put them back if less than 100
        if (!sessionId || !studentId) {
            if (this.buffer.length < 100) {
                this.buffer = [...logsToSend, ...this.buffer];
            }
            return;
        }

        try {
            const res = await fetch(`${API_BASE_URL}/api/logs/batch`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    student_id: studentId,
                    browser_fingerprint: this.browserFingerprint,
                    logs: logsToSend
                }),
                // Keep-alive for beforeunload cases
                keepalive: true
            });

            if (!res.ok) {
                throw new Error("Log upload failed");
            }
        } catch (e) {
            console.error("TestLogger error: Could not flush logs", e);
            // Put failed logs back into the buffer if it's not too crowded
            if (this.buffer.length < 200) {
                this.buffer = [...logsToSend, ...this.buffer];
            }
        }
    }
}

// Singleton export
export const testLogger = new TestLogger();
