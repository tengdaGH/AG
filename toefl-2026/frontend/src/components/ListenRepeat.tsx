import React, { useState, useEffect, useRef } from 'react';
import { useLanguage } from '@/lib/i18n/LanguageContext';
import { useMediaRecorderChunking } from '../hooks/useMediaRecorderChunking';

export interface ListenRepeatProps {
    imageUrl: string;
    imageAlt?: string;
    audioUrl?: string;     // URL for the stimulus audio
    questionId: string;
    sessionId: string;
    uploadUrl: string;
    onComplete?: () => void;
    onAudioEnd?: () => void;
}

export function ListenRepeat({ imageUrl, imageAlt = "Listen and repeat context", audioUrl, questionId, sessionId, uploadUrl, onComplete, onAudioEnd }: ListenRepeatProps) {
    const { t } = useLanguage();
    const [state, setState] = useState<'LISTENING' | 'BEEP' | 'RECORDING' | 'DONE'>('LISTENING');
    const [secondsLeft, setSecondsLeft] = useState(15); // Adjust time here if necessary
    const audioRef = useRef<HTMLAudioElement>(null);
    const audioContextRef = useRef<AudioContext | null>(null);

    // The secure WebRTC audio chunking protocol
    const { isRecording, startRecording, stopRecording } = useMediaRecorderChunking(uploadUrl, questionId, sessionId);
    const translation = t('test.listenAndRepeatOnlyOnce');
    const instructionText = translation === 'test.listenAndRepeatOnlyOnce' ? 'Listen and repeat only once.' : translation;

    // Play 500ms synthesized 800Hz sine beep, identical to ETS signature
    const playETSBeep = () => {
        setState('BEEP');
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

    useEffect(() => {
        if (state === 'LISTENING' && audioUrl && audioRef.current) {
            audioRef.current.play().catch(e => console.warn("Auto-play prevented:", e));

            const handleEnded = () => {
                playETSBeep();
            };
            const currentAudio = audioRef.current;
            currentAudio.addEventListener('ended', handleEnded);

            return () => {
                currentAudio.removeEventListener('ended', handleEnded);
            };
        }
    }, [audioUrl, state]);

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
            onAudioEnd?.();
            if (onComplete) {
                setTimeout(() => onComplete(), 1500); // Wait 1.5s to show 'Done'
            }
        }
    }, [state, secondsLeft, stopRecording, onAudioEnd, onComplete]);

    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'flex-start',
            width: '100%',
            height: '100%',
            backgroundColor: '#FFFFFF',
            border: '1px solid #767676',
            boxSizing: 'border-box',
            padding: '80px 20px', // More vertical space to match Figure 11
            fontFamily: 'Arial, sans-serif' // Standard ETS sans-serif for instructions
        }}>

            {/* Instructional Header */}
            <h2 style={{
                color: '#137882', // Darker ETS Teal matching Figure 11 closely
                fontSize: '28px',
                fontWeight: 'bold',
                fontFamily: '"Times New Roman", Times, serif', // Figure 11 uses a serif font for this specific instruction
                margin: '0 0 60px 0',
                textAlign: 'center'
            }}>
                {instructionText}
            </h2>

            {/* Contextual Image Container */}
            <div style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                maxWidth: '600px', // Restrict image width to maintain ratio and match mockup
                width: '100%'
            }}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                    src={imageUrl}
                    alt={imageAlt}
                    style={{
                        width: '100%',
                        height: 'auto',
                        border: '1px solid #767676', // Match the outer container border color exactly for a flat, formal look
                        display: 'block'
                    }}
                />
            </div>

            {/* Test Status Indicators */}
            <div style={{ marginTop: '40px', height: '100px', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                {state === 'LISTENING' && (
                    <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '40px', marginBottom: '8px' }}>🎧</div>
                        <div style={{ color: '#005587', fontSize: '18px', fontWeight: 'bold' }}>Now Listening...</div>
                    </div>
                )}
                {state === 'RECORDING' && (
                    <div style={{ textAlign: 'center' }}>
                        <div style={{
                            fontSize: '40px', fontWeight: 'bold', color: '#D32F2F', fontVariantNumeric: 'tabular-nums',
                            animation: 'pulse 2s infinite', marginBottom: '8px'
                        }}>
                            00:{secondsLeft.toString().padStart(2, '0')}
                        </div>
                        <div style={{ color: '#D32F2F', fontSize: '18px', fontWeight: 'bold' }}>
                            🎙️ Now Recording...
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
                {state === 'DONE' && (
                    <div style={{ textAlign: 'center', color: '#388E3C', fontSize: '18px', fontWeight: 'bold' }}>
                        ✓ Response Recorded
                    </div>
                )}
            </div>

            {
                audioUrl && (
                    <audio
                        ref={audioRef}
                        src={audioUrl}
                        style={{ display: 'none' }}
                    />
                )
            }

        </div >
    );
}
