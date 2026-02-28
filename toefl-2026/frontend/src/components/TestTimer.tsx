'use client';

import React, { useState, useEffect } from 'react';

interface TestTimerProps {
    expirationMs?: number | null;
    fallbackSeconds?: number;
    onTimeUp?: () => void;
    sectionName?: string;
}

export const TestTimer: React.FC<TestTimerProps> = ({
    expirationMs,
    fallbackSeconds = 0,
    onTimeUp
}) => {
    const [secondsLeft, setSecondsLeft] = useState(() => {
        if (!expirationMs) return fallbackSeconds;
        return Math.max(0, Math.floor((expirationMs - Date.now()) / 1000));
    });
    const [isHidden, setIsHidden] = useState(false);
    const [isFlashing, setIsFlashing] = useState(false);

    useEffect(() => {
        if (secondsLeft <= 0) {
            if (onTimeUp) onTimeUp();
            return;
        }

        const timerId = setInterval(() => {
            setSecondsLeft((prev) => {
                let next;
                if (expirationMs) {
                    next = Math.floor((expirationMs - Date.now()) / 1000);
                } else {
                    next = prev - 1;
                }
                return Math.max(0, next);
            });
        }, 1000);

        return () => clearInterval(timerId);
    }, [secondsLeft, onTimeUp, expirationMs]);

    // Format time as MM:SS
    const formatTime = (totalSeconds: number) => {
        const m = Math.floor(totalSeconds / 60);
        const s = totalSeconds % 60;
        return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    };

    const isDanger = secondsLeft <= 300; // Less than or equal to 5 minutes

    useEffect(() => {
        if (secondsLeft === 300) {
            // Exactly 5 minutes: force show time and flash
            setIsHidden(false);

            // Flash 3 times
            let flashCount = 0;
            const flashInterval = setInterval(() => {
                setIsFlashing((prev) => !prev);
                flashCount++;
                if (flashCount >= 6) { // 3 times (on/off)
                    clearInterval(flashInterval);
                    setIsFlashing(false);
                }
            }, 500);
        }
    }, [secondsLeft]);

    const timerColor = isDanger ? '#EF4444' : '#FFFFFF';

    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            {isHidden && !isDanger ? (
                <div style={{
                    fontSize: '16px',
                    fontWeight: 700,
                    color: '#FFFFFF',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '5px'
                }}>
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="12" cy="12" r="10"></circle>
                        <polyline points="12 6 12 12 16 14"></polyline>
                    </svg>
                </div>
            ) : (
                <div
                    style={{
                        fontSize: '16px',
                        fontWeight: 700,
                        fontVariantNumeric: 'tabular-nums',
                        color: timerColor,
                        opacity: isFlashing ? 0.5 : 1,
                        transition: 'opacity 0.2s'
                    }}
                >
                    {formatTime(secondsLeft)}
                </div>
            )}
            <button
                onClick={() => setIsHidden(!isHidden)}
                disabled={isDanger}
                style={{
                    background: 'none',
                    border: '1px solid rgba(255,255,255,0.4)',
                    borderRadius: '20px',
                    fontSize: '10px',
                    fontWeight: 600,
                    padding: '2px 8px',
                    marginTop: '4px',
                    cursor: isDanger ? 'not-allowed' : 'pointer',
                    color: '#FFFFFF',
                    opacity: isDanger ? 0.5 : 0.8
                }}
            >
                {isHidden && !isDanger ? 'Show Time' : 'Hide Time'}
            </button>
        </div>
    );
};
