'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useMediaRecorderChunking } from '../hooks/useMediaRecorderChunking';

interface InterviewUIProps {
    promptVideoUrl: string; // The specific question MP4
    maxRecordTimeSeconds: number; // usually 45
    websocketUrl: string;
}

export const InterviewUI: React.FC<InterviewUIProps> = ({
    promptVideoUrl,
    maxRecordTimeSeconds,
    websocketUrl
}) => {
    // idle -> prompt -> recording -> done
    const [state, setState] = useState<'IDLE' | 'PROMPT' | 'RECORDING' | 'DONE'>('IDLE');
    const [secondsLeft, setSecondsLeft] = useState(maxRecordTimeSeconds);
    const videoRef = useRef<HTMLVideoElement>(null);
    const audioContextRef = useRef<AudioContext | null>(null);

    // The secure WebRTC audio chunking protocol
    const { isRecording, startRecording, stopRecording } = useMediaRecorderChunking(websocketUrl);

    // Play 500ms synthesized 800Hz sine beep, identical to ETS signature
    const playETSBeep = () => {
        if (!audioContextRef.current) {
            audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
        }
        const osc = audioContextRef.current.createOscillator();
        const gainNode = audioContextRef.current.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(800, audioContextRef.current.currentTime);

        osc.connect(gainNode);
        gainNode.connect(audioContextRef.current.destination);

        osc.start();
        osc.stop(audioContextRef.current.currentTime + 0.5); // 500ms playback

        // Once the beep finishes, recording state unlocks
        setTimeout(() => {
            setState('RECORDING');
            startRecording();
        }, 500);
    };

    const handleVideoEnded = () => {
        if (state === 'PROMPT') {
            // Cutover: the exact millisecond the prompt ends, transition and beep.
            playETSBeep();
        }
    };

    const startPrompt = () => {
        setState('PROMPT');
        if (videoRef.current) {
            videoRef.current.loop = false; // Stop idle looping
            videoRef.current.src = promptVideoUrl;
            videoRef.current.play().catch(e => console.warn("Video blocked:", e));
        }
    };

    // Timer sync for the recording phase
    useEffect(() => {
        if (state === 'RECORDING' && secondsLeft > 0) {
            const timer = setTimeout(() => {
                setSecondsLeft(prev => prev - 1);
            }, 1000);
            return () => clearTimeout(timer);
        } else if (state === 'RECORDING' && secondsLeft <= 0) {
            setState('DONE');
            stopRecording();
        }
    }, [state, secondsLeft, stopRecording]);

    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            backgroundColor: '#FFFFFF',
            border: '1px solid #767676',
            boxSizing: 'border-box',
            padding: '80px 20px',
            fontFamily: 'Arial, Helvetica, sans-serif'
        }}>

            <h2 style={{
                color: '#137882',
                marginBottom: '40px',
                fontSize: '28px',
                fontWeight: 'bold',
                fontFamily: '"Times New Roman", Times, serif',
                textAlign: 'center'
            }}>
                {state === 'IDLE' && 'Interviewer is connecting...'}
                {state === 'PROMPT' && "Please answer the interviewer's questions."}
                {state === 'RECORDING' && "Please answer the interviewer's questions."}
                {state === 'DONE' && 'Response recorded.'}
            </h2>

            {/* Simulated Live Interviewer Video */}
            <div style={{
                width: '640px', height: '360px', backgroundColor: '#000',
                border: '1px solid #767676',
                overflow: 'hidden', position: 'relative', marginBottom: '40px'
            }}>
                <video
                    ref={videoRef}
                    playsInline
                    disablePictureInPicture
                    controlsList="nodownload nofullscreen noremoteplayback"
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    onEnded={handleVideoEnded}
                >
                    {/* Simulated idle breathing loops could be preloaded here */}
                    <source src="/legacy_idle_loop.mp4" type="video/mp4" />
                </video>
            </div>

            {/* Test Simulation Controls (Only for Demo purposes, normally triggered by test sequencer) */}
            {state === 'IDLE' && (
                <button
                    onClick={startPrompt}
                    style={{ backgroundColor: '#005587', color: '#FFF', padding: '10px 20px', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
                >
                    Start AI Prompt
                </button>
            )}

            {/* The Massive Central Recording Timer & Indicator */}
            {state === 'RECORDING' && (
                <div style={{ textAlign: 'center' }}>
                    <div style={{
                        fontSize: '48px', fontWeight: 'bold', color: '#D32F2F', fontVariantNumeric: 'tabular-nums',
                        animation: 'pulse 2s infinite'
                    }}>
                        00:{secondsLeft.toString().padStart(2, '0')}
                    </div>
                    <div style={{ color: '#D32F2F', fontSize: '18px', fontWeight: 'bold', marginTop: '10px' }}>
                        ● RECORDING
                    </div>

                    <style dangerouslySetInnerHTML={{
                        __html: `
                        @keyframes pulse {
                            0% { opacity: 1; }
                            50% { opacity: 0.5; }
                            100% { opacity: 1; }
                        }
                    `}} />
                </div>
            )}
        </div>
    );
};
