'use client';

import React, { useState, useEffect, useRef } from 'react';

interface SpeakingVisualizerProps {
    promptAudioUrl?: string; // Optional interviewer question
    maxRecordTimeSeconds: number;
    onRecordingComplete: (audioBlob: Blob) => void;
}

export const SpeakingVisualizer: React.FC<SpeakingVisualizerProps> = ({
    promptAudioUrl,
    maxRecordTimeSeconds,
    onRecordingComplete
}) => {
    const [audioState, setAudioState] = useState<'LISTENING' | 'RECORDING' | 'DONE'>('LISTENING');
    const [secondsLeft, setSecondsLeft] = useState(maxRecordTimeSeconds);
    const [volume, setVolume] = useState(0); // 0 to 100

    const audioContextRef = useRef<AudioContext | null>(null);
    const analyzerRef = useRef<AnalyserNode | null>(null);
    const microphoneRef = useRef<MediaStreamAudioSourceNode | null>(null);
    const animationFrameRef = useRef<number>(0);
    const promptAudioRef = useRef<HTMLAudioElement | null>(null);

    const playBeep = () => {
        if (!audioContextRef.current) {
            audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
        }
        const osc = audioContextRef.current.createOscillator();
        const gainNode = audioContextRef.current.createGain();
        osc.type = 'sine';
        osc.frequency.value = 800; // 800Hz ETS beep signature
        osc.connect(gainNode);
        gainNode.connect(audioContextRef.current.destination);
        osc.start();

        // Beep duration 500ms
        setTimeout(() => {
            osc.stop();
            startRecording();
        }, 500);
    };

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            if (!audioContextRef.current) {
                audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
            }

            analyzerRef.current = audioContextRef.current.createAnalyser();
            analyzerRef.current.fftSize = 256;

            microphoneRef.current = audioContextRef.current.createMediaStreamSource(stream);
            microphoneRef.current.connect(analyzerRef.current);

            setAudioState('RECORDING');
            visualizeVolume();

            // Simulate MediaRecorder timeslice functionality via mock 
            // In full execution, MediaRecorder captures slices dynamically
        } catch (err) {
            console.error("Microphone access denied or error:", err);
            // ETS Fallback warning required here
        }
    };

    const visualizeVolume = () => {
        if (!analyzerRef.current) return;

        const dataArray = new Uint8Array(analyzerRef.current.frequencyBinCount);
        analyzerRef.current.getByteFrequencyData(dataArray);

        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
            sum += dataArray[i];
        }

        const avg = sum / dataArray.length;
        // Map average (0 - 255) to volume % (0 - 100)
        setVolume(Math.min(100, Math.round((avg / 255) * 100 * 1.5))); // 1.5 multiplier for visibility

        animationFrameRef.current = requestAnimationFrame(visualizeVolume);
    };

    useEffect(() => {
        if (promptAudioUrl) {
            promptAudioRef.current = new Audio(promptAudioUrl);
            promptAudioRef.current.onended = () => {
                playBeep();
            };
            promptAudioRef.current.play().catch(e => console.warn("Auto-play blocked", e));
        } else {
            // No prompt, jump directly to beep then record for tasks like "Listen and Repeat" after image
            setTimeout(playBeep, 2000);
        }

        return () => {
            if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
            if (promptAudioRef.current) promptAudioRef.current.pause();
        };
    }, [promptAudioUrl]);

    // Countdown Timer logic
    useEffect(() => {
        if (audioState === 'RECORDING' && secondsLeft > 0) {
            const timer = setTimeout(() => {
                setSecondsLeft(prev => prev - 1);
            }, 1000);
            return () => clearTimeout(timer);
        } else if (audioState === 'RECORDING' && secondsLeft <= 0) {
            setAudioState('DONE');
            if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
            // End recording and return blob
        }
    }, [audioState, secondsLeft]);

    // Calculate Volume Bar Color (Green -> Yellow -> Red)
    const getBarColor = () => {
        if (volume < 40) return '#4ade80'; // Green
        if (volume < 80) return '#facc15'; // Yellow
        return '#f87171'; // Red
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: audioState === 'RECORDING' ? '#D32F2F' : '#212121', marginBottom: '30px' }}>
                {audioState === 'LISTENING' ? 'Listening...' : audioState === 'RECORDING' ? 'Recording...' : 'Completed'}
            </div>

            {/* Simulated Live Audio Meter */}
            <div style={{
                width: '300px',
                height: '40px',
                backgroundColor: '#F4F5F7',
                border: '2px solid #D1D6E0',
                borderRadius: '20px',
                overflow: 'hidden',
                position: 'relative',
                marginBottom: '20px'
            }}>
                <div style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    height: '100%',
                    width: `${volume}%`,
                    backgroundColor: getBarColor(),
                    transition: 'width 0.1s ease-out, background-color 0.2s',
                }} />
            </div>

            {audioState === 'RECORDING' && (
                <div style={{ fontSize: '20px', fontWeight: 600, color: '#D32F2F', fontVariantNumeric: 'tabular-nums' }}>
                    00:{secondsLeft.toString().padStart(2, '0')}
                </div>
            )}
        </div>
    );
};
