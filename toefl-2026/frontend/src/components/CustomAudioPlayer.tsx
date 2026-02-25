'use client';

import React, { useRef, useState, useEffect } from 'react';

interface CustomAudioPlayerProps {
    src: string;
    onEnded: () => void;
    autoPlay?: boolean;
    resumeFromMs?: number; // Used for ETS crash recovery penalty
}

export const CustomAudioPlayer: React.FC<CustomAudioPlayerProps> = ({
    src,
    onEnded,
    autoPlay = true,
    resumeFromMs = 0
}) => {
    const audioRef = useRef<HTMLAudioElement>(null);
    const [progress, setProgress] = useState(0);

    useEffect(() => {
        if (!audioRef.current) return;

        const updateProgress = () => {
            if (audioRef.current && audioRef.current.duration) {
                const current = audioRef.current.currentTime;
                const total = audioRef.current.duration;
                setProgress((current / total) * 100);
            }
            requestAnimationFrame(updateProgress);
        };

        const handleCanPlay = () => {
            if (audioRef.current && resumeFromMs > 0) {
                // Crash recovery logic: Subtract 3 seconds (3000ms) for context resumption
                const resumeTarget = Math.max(0, (resumeFromMs - 3000) / 1000);
                audioRef.current.currentTime = resumeTarget;
            }
            if (autoPlay && audioRef.current) {
                audioRef.current.play().catch(e => console.warn('Autoplay blocked:', e));
            }
        };

        const handleEnded = () => {
            onEnded();
        };

        const animFrame = requestAnimationFrame(updateProgress);

        audioRef.current.addEventListener('canplay', handleCanPlay);
        audioRef.current.addEventListener('ended', handleEnded);

        return () => {
            cancelAnimationFrame(animFrame);
            if (audioRef.current) {
                audioRef.current.removeEventListener('canplay', handleCanPlay);
                audioRef.current.removeEventListener('ended', handleEnded);
            }
        };
    }, [src, autoPlay, resumeFromMs, onEnded]);

    return (
        <div style={{ width: '100%', maxWidth: '600px', margin: '20px auto' }}>
            {/* Hidden native player to prevent manual controls / scrubbing */}
            <audio ref={audioRef} src={src} preload="auto" />

            {/* Custom Unscrubbable ETS Progress Bar */}
            <div style={{
                height: '10px',
                width: '100%',
                backgroundColor: '#D1D6E0', // ETS Gray
                borderRadius: '5px',
                overflow: 'hidden',
                pointerEvents: 'none' // STRICT: Clicking progress bar does absolutely nothing
            }}>
                <div style={{
                    height: '100%',
                    width: `${progress}%`,
                    backgroundColor: '#005587', // ETS Primary Blue
                    transition: 'width 0.1s linear'
                }} />
            </div>
            <div style={{ fontSize: '12px', color: '#5E6A75', marginTop: '8px', textAlign: 'center' }}>
                Audio is playing. You cannot pause or replay the audio.
            </div>
        </div>
    );
};
