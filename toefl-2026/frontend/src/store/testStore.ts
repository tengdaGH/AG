import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { API_BASE_URL } from '@/lib/api-config';

interface TestState {
    sessionId: string | null;
    studentId: string | null;
    answers: Record<string, string>; // Maps question_id to student's raw response
    isSubmitting: boolean;

    // --- Resumption State ---
    phase: string;
    items: any[];
    idx: number;
    secIdx: number;
    expirationTimeMs: number | null; // For robust timer resumption

    setSessionId: (id: string) => void;
    setStudentId: (id: string) => void;
    setAnswer: (questionId: string, answer: string) => void;

    setTestState: (partial: Partial<TestState>) => void;
    clearSession: () => void;

    submitTest: () => Promise<void>;
}

export const useTestStore = create<TestState>()(
    persist(
        (set, get) => ({
            sessionId: null,
            studentId: null,
            answers: {},
            isSubmitting: false,

            phase: 'LOADING',
            items: [],
            idx: 0,
            secIdx: 0,
            expirationTimeMs: null,

            setSessionId: (id) => set({ sessionId: id }),
            setStudentId: (id) => set({ studentId: id }),

            setAnswer: (questionId, answer) => set((state) => ({
                answers: {
                    ...state.answers,
                    [questionId]: answer
                }
            })),

            setTestState: (partial) => set((state) => ({ ...state, ...partial })),

            clearSession: () => set({
                sessionId: null,
                answers: {},
                phase: 'LOADING',
                items: [],
                idx: 0,
                secIdx: 0,
                expirationTimeMs: null,
                isSubmitting: false
            }),

            submitTest: async () => {
                const { sessionId, answers } = get();
                if (!sessionId) {
                    console.error("No active session to submit.");
                    return;
                }

                set({ isSubmitting: true });
                try {
                    // Send the giant dictionary to our new API route
                    const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/submit`, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "Bypass-Tunnel-Reminder": "true"
                        },
                        body: JSON.stringify({ answers })
                    });

                    if (!response.ok) {
                        throw new Error("Failed to submit test.");
                    }

                    const data = await response.json();
                    console.log("Submission successful:", data);

                    // Add an artificial 5-second "breathing room" delay
                    // so the user sees the "AI is analyzing" animation.
                    await new Promise(resolve => setTimeout(resolve, 5000));

                    // We can route to a results view from the component
                    set({ isSubmitting: false });
                } catch (error) {
                    console.error("Error submitting test:", error);
                    set({ isSubmitting: false });
                }
            }
        }),
        {
            name: 'ets-test-storage', // name of the item in the storage (must be unique)
            storage: createJSONStorage(() => localStorage),
        }
    )
);
