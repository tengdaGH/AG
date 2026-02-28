'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/Button';
import { Card, CardContent } from '@/components/Card';
import { evaluateSpeakingResponse } from '@/lib/scoring-engine/ai-scorer';
import { useLanguage } from '@/lib/i18n/LanguageContext';

type SpeakingPhase = 'INSTRUCTIONS' | 'PREPARATION' | 'RECORDING' | 'COMPLETED';

export default function VirtualInterviewTask() {
    const router = useRouter();
    const { t } = useLanguage();
    const [phase, setPhase] = useState<SpeakingPhase>('INSTRUCTIONS');
    const [prepSecondsLeft, setPrepSecondsLeft] = useState(15);
    const [recordingSecondsLeft, setRecordingSecondsLeft] = useState(45);
    const [audioLevel, setAudioLevel] = useState(0);

    // Simulated audio level meter during recording
    useEffect(() => {
        let interval: NodeJS.Timeout;
        if (phase === 'RECORDING') {
            interval = setInterval(() => {
                // Random value between 10 and 90 to simulate speaking volume
                setAudioLevel(Math.floor(Math.random() * 80) + 10);
            }, 150);
        } else {
            setAudioLevel(0);
        }
        return () => clearInterval(interval);
    }, [phase]);

    // Phase timers
    useEffect(() => {
        let prepInterval: NodeJS.Timeout;
        let recInterval: NodeJS.Timeout;

        if (phase === 'PREPARATION') {
            prepInterval = setInterval(() => {
                setPrepSecondsLeft((prev) => {
                    if (prev <= 1) {
                        setPhase('RECORDING');
                        return 0;
                    }
                    return prev - 1;
                });
            }, 1000);
        } else if (phase === 'RECORDING') {
            recInterval = setInterval(() => {
                setRecordingSecondsLeft((prev) => {
                    if (prev <= 1) {
                        setPhase('COMPLETED');
                        return 0;
                    }
                    return prev - 1;
                });
            }, 1000);
        }

        return () => {
            clearInterval(prepInterval);
            clearInterval(recInterval);
        };
    }, [phase]);

    const [isScoring, setIsScoring] = useState(false);

    const handleStartPrep = () => {
        setPhase('PREPARATION');
    };

    const handleNextSection = async () => {
        setIsScoring(true);
        // Simulate grading the recorded audio
        const score = await evaluateSpeakingResponse('/mock/audio/path.webm');
        setIsScoring(false);

        alert(`${t('test.speakingCompletedAlert1')} ${score.bandScore} (${score.cefrLevel})\nRouting to Writing Section...`);
        router.push('/test-session/demo/writing');
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', backgroundColor: '#f1f5f9' }}>
            <header style={{
                backgroundColor: '#1e293b',
                color: 'white',
                padding: '0.75rem 2rem',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                    <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>TOEFL iBT</div>
                    <div style={{ padding: '0.25rem 0.75rem', backgroundColor: '#334155', borderRadius: '4px', fontSize: '0.875rem' }}>
                        {t('test.speakingSectionVirtual')}
                    </div>
                </div>

                {phase === 'PREPARATION' && (
                    <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase' }}>{t('test.preparationTime')}</div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>00:{prepSecondsLeft.toString().padStart(2, '0')}</div>
                    </div>
                )}

                {phase === 'RECORDING' && (
                    <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#ef4444', textTransform: 'uppercase' }}>{t('test.recordingActive')}</div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#ef4444' }}>00:{recordingSecondsLeft.toString().padStart(2, '0')}</div>
                    </div>
                )}

                {phase === 'INSTRUCTIONS' || phase === 'COMPLETED' ? (
                    <div style={{ width: '150px' }}></div> // Spacer for layout balance
                ) : null}

                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{ fontSize: '0.875rem', color: '#cbd5e1' }}>{t('test.task1Of2')}</div>
                    <div title={t('test.connectionStable')} style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#22c55e' }}></div>
                </div>
            </header>

            <main style={{ flex: 1, padding: '2rem', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
                <Card style={{ width: '100%', maxWidth: '800px', overflow: 'hidden' }}>

                    {/* Simulated Video Feed Area */}
                    <div style={{
                        width: '100%',
                        height: '400px',
                        backgroundColor: '#0f172a',
                        position: 'relative',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                    }}>
                        {/* Replace with actual video tag in production */}
                        <div style={{
                            width: '120px',
                            height: '120px',
                            borderRadius: '50%',
                            backgroundColor: '#334155',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: 'white',
                            fontSize: '3rem'
                        }}>
                            👤
                        </div>

                        {/* Simulated Subtitles/Prompt (appears during question) */}
                        <div style={{
                            position: 'absolute',
                            bottom: '2rem',
                            left: '2rem',
                            right: '2rem',
                            padding: '1rem',
                            backgroundColor: 'rgba(0,0,0,0.7)',
                            color: 'white',
                            borderRadius: '8px',
                            fontSize: '1.125rem',
                            textAlign: 'center',
                            border: '1px solid rgba(255,255,255,0.2)'
                        }}>
                            "Some students prefer classes where the professor lectures entirely, while others prefer classes that include discussion. Which do you prefer and why?"
                        </div>
                    </div>

                    <CardContent style={{ padding: '2rem', backgroundColor: '#fff', borderTop: '1px solid #e2e8f0' }}>

                        {phase === 'INSTRUCTIONS' && (
                            <div style={{ textAlign: 'center' }}>
                                <h2 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '1rem' }}>{t('test.listenToQuestion')}</h2>
                                <p style={{ color: '#475569', marginBottom: '2rem' }}>{t('test.speakPrepInstructions')}</p>
                                <Button size="lg" onClick={handleStartPrep}>{t('test.startTask')}</Button>
                            </div>
                        )}

                        {phase === 'PREPARATION' && (
                            <div style={{ textAlign: 'center' }}>
                                <h2 style={{ fontSize: '1.5rem', fontWeight: 600, color: '#f59e0b', marginBottom: '0.5rem' }}>{t('test.prepareResponse')}</h2>
                                <p style={{ color: '#475569' }}>{t('test.recordingBeginsAuto')}</p>
                            </div>
                        )}

                        {phase === 'RECORDING' && (
                            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.5rem' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                    <div style={{ width: '16px', height: '16px', borderRadius: '50%', backgroundColor: '#ef4444', animation: 'pulse 1.5s infinite' }}></div>
                                    <span style={{ fontSize: '1.25rem', fontWeight: 600, color: '#ef4444' }}>{t('test.recording')}</span>
                                </div>

                                {/* Audio Level Meter */}
                                <div style={{ width: '100%', maxWidth: '400px', height: '12px', backgroundColor: '#e2e8f0', borderRadius: '9999px', overflow: 'hidden' }}>
                                    <div style={{
                                        height: '100%',
                                        width: `${audioLevel}%`,
                                        backgroundColor: audioLevel > 80 ? '#ef4444' : audioLevel > 50 ? '#10b981' : '#3b82f6',
                                        transition: 'width 0.1s ease-out, background-color 0.2s'
                                    }}></div>
                                </div>
                                <p style={{ fontSize: '0.875rem', color: '#64748b' }}>{t('test.speakClearly')}</p>
                            </div>
                        )}

                        {phase === 'COMPLETED' && (
                            <div style={{ textAlign: 'center' }}>
                                <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>✅</div>
                                <h2 style={{ fontSize: '1.5rem', fontWeight: 600, color: '#16a34a', marginBottom: '0.5rem' }}>{t('test.responseRecorded')}</h2>
                                <p style={{ color: '#475569', marginBottom: '2rem' }}>{t('test.audioUploaded')}</p>
                                <Button size="lg" onClick={handleNextSection} disabled={isScoring}>
                                    {isScoring ? t('test.processingAudio') : t('test.completeTest')}
                                </Button>
                            </div>
                        )}

                    </CardContent>
                </Card>
            </main>

            {/* Inline styles for pulse animation */}
            <style dangerouslySetInnerHTML={{
                __html: `
        @keyframes pulse {
          0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
          70% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }
          100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
        }
      `}} />
        </div>
    );
}
