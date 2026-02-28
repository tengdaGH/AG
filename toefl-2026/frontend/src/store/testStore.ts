import { create } from 'zustand';

interface TestState {
    sessionId: string | null;
    studentId: string | null;
    answers: Record<string, string>; // Maps question_id to student's raw response
    isSubmitting: boolean;

    setSessionId: (id: string) => void;
    setStudentId: (id: string) => void;
    setAnswer: (questionId: string, answer: string) => void;
    submitTest: () => Promise<void>;
}

export const useTestStore = create<TestState>((set, get) => ({
    sessionId: null,
    studentId: null,
    answers: {},
    isSubmitting: false,

    setSessionId: (id) => set({ sessionId: id }),
    setStudentId: (id) => set({ studentId: id }),

    setAnswer: (questionId, answer) => set((state) => ({
        answers: {
            ...state.answers,
            [questionId]: answer
        }
    })),

    submitTest: async () => {
        const { sessionId, answers } = get();
        if (!sessionId) {
            console.error("No active session to submit.");
            return;
        }

        set({ isSubmitting: true });
        try {
            // Send the giant dictionary to our new API route
            const response = await fetch(`http://localhost:8000/api/sessions/${sessionId}/submit`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ answers })
            });

            if (!response.ok) {
                throw new Error("Failed to submit test.");
            }

            const data = await response.json();
            console.log("Submission successful:", data);

            // We can route to a results view from the component
            set({ isSubmitting: false });
        } catch (error) {
            console.error("Error submitting test:", error);
            set({ isSubmitting: false });
        }
    }
}));
