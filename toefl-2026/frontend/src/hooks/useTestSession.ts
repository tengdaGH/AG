import { useState, useEffect, useRef } from 'react';

export interface TestState {
    ets_id: string;
    current_section: string;
    adaptive_stage: number;
    current_item_index: number;
    time_remaining_ms: number;
    responses: Record<string, string>;
    audio_progress_ms: number;
    writing_content?: string;
    last_updated?: number;
}

const STORAGE_KEY = 'ets_antigravity_session';
const SYNC_INTERVAL_MS = 5000;

export const useTestSession = (initialState: Partial<TestState>) => {
    const [testState, setTestState] = useState<TestState>(() => {
        // Attempt local recovery first
        if (typeof window !== 'undefined') {
            const saved = localStorage.getItem(STORAGE_KEY);
            if (saved) {
                try {
                    const parsed = JSON.parse(saved) as TestState;
                    // Apply 30-second ETS disconnect penalty if we recovered
                    // Or for audio resumption, we handle that specifically in the UI component
                    if (parsed.time_remaining_ms > 30000) {
                        parsed.time_remaining_ms -= 30000;
                    }
                    console.warn("Session restored. 30 second disconnect penalty applied.");
                    return parsed;
                } catch (e) {
                    console.error("Failed to parse restored session", e);
                }
            }
        }

        return {
            ets_id: 'UNKNOWN',
            current_section: 'Reading',
            adaptive_stage: 1,
            current_item_index: 0,
            time_remaining_ms: 85 * 60 * 1000,
            responses: {},
            audio_progress_ms: 0,
            writing_content: '',
            ...initialState
        };
    });

    const stateRef = useRef(testState);

    // Keep ref synced for interval access without re-binding
    useEffect(() => {
        stateRef.current = testState;
    }, [testState]);

    // Update individual state pieces
    const updateState = (updates: Partial<TestState>) => {
        setTestState(prev => ({
            ...prev,
            ...updates,
            last_updated: Date.now()
        }));
    };

    const updateResponse = (itemId: string, value: string) => {
        setTestState(prev => ({
            ...prev,
            responses: {
                ...prev.responses,
                [itemId]: value
            },
            last_updated: Date.now()
        }));
    };

    // Auto-save and Background API Sync Look
    useEffect(() => {
        const syncInterval = setInterval(() => {
            const currentState = stateRef.current;
            localStorage.setItem(STORAGE_KEY, JSON.stringify(currentState));

            // Silent background API call
            fetch('/api/v1/session/sync_state', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(currentState),
            }).catch(() => {
                // Silently swallow errors as test timer continues regardless
                console.warn('Sync state network error, fallback to IndexedDB/localStorage active.');
            });

        }, SYNC_INTERVAL_MS);

        return () => clearInterval(syncInterval);
    }, []);

    // Clear session at the end of the test
    const clearSession = () => {
        localStorage.removeItem(STORAGE_KEY);
    };

    return {
        testState,
        updateState,
        updateResponse,
        clearSession
    };
};
