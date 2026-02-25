'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { TestTimer } from '@/components/TestTimer';
import { Button } from '@/components/Button';
import { Card, CardContent } from '@/components/Card';
import { useLanguage } from '@/lib/i18n/LanguageContext';

type ListeningPhase = 'DIRECTIONS' | 'PLAYING_AUDIO' | 'ANSWERING';

export default function ListeningTestEngine() {
    const router = useRouter();
    const { t } = useLanguage();
    const [phase, setPhase] = useState<ListeningPhase>('DIRECTIONS');
    const [audioProgress, setAudioProgress] = useState(0);
    const [currentQuestion, setCurrentQuestion] = useState(1);
    const totalQuestionsBlock1 = 3;

    // Simulate audio playback progress
    useEffect(() => {
        let interval: NodeJS.Timeout;
        if (phase === 'PLAYING_AUDIO') {
            interval = setInterval(() => {
                setAudioProgress((prev) => {
                    if (prev >= 100) {
                        setPhase('ANSWERING');
                        return 100;
                    }
                    return prev + 1.25; // Simulate ~80s audio clip
                });
            }, 1000);
        }
        return () => clearInterval(interval);
    }, [phase]);

    const handleStartAudio = () => {
        setPhase('PLAYING_AUDIO');
        setAudioProgress(0);
    };

    const handleNextQuestion = () => {
        if (currentQuestion < totalQuestionsBlock1) {
            setCurrentQuestion(c => c + 1);
        } else {
            alert(t('test.listeningCompleteAlert'));
            router.push('/test-session/demo/speaking');
        }
    };

    const handleTimeUp = () => {
        alert(t('test.timeUpAlert'));
        router.push('/test-session/demo/speaking');
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
                        {t('test.listeningStage1')}
                    </div>
                </div>

                {phase === 'ANSWERING' ? (
                    <TestTimer initialSeconds={600} onTimeUp={handleTimeUp} sectionName={t('test.answeringTime')} />
                ) : (
                    <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase' }}>{t('test.volumeCheck')}</div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#94a3b8' }}>--:--</div>
                    </div>
                )}

                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    {phase === 'ANSWERING' && <div style={{ fontSize: '0.875rem', color: '#cbd5e1' }}>{t('test.question')} {currentQuestion} / {totalQuestionsBlock1}</div>}
                    <div title={t('test.connectionStable')} style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#22c55e' }}></div>
                </div>
            </header>

            <main style={{ flex: 1, padding: '2rem', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
                <Card style={{ width: '100%', maxWidth: '900px', overflow: 'hidden' }}>

                    {/* Top Panel: Audio Context Image */}
                    {(phase === 'DIRECTIONS' || phase === 'PLAYING_AUDIO') && (
                        <div style={{
                            width: '100%',
                            height: '350px',
                            backgroundColor: '#e2e8f0',
                            position: 'relative',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            borderBottom: '1px solid #cbd5e1'
                        }}>
                            {/* Image Placeholder representing Professor in classroom */}
                            <div style={{ textAlign: 'center', color: '#64748b' }}>
                                <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>👨‍🏫 🏛️</div>
                                <div style={{ fontSize: '1.25rem', fontWeight: 500 }}>{t('test.academicLecture')}</div>
                            </div>

                            {/* Progress Bar Overlay */}
                            {phase === 'PLAYING_AUDIO' && (
                                <div style={{ position: 'absolute', bottom: '2rem', left: '10%', right: '10%', backgroundColor: 'rgba(255,255,255,0.9)', padding: '1.5rem', borderRadius: '12px', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: 600 }}>
                                        <span>{t('test.playingAudio')} ({Math.floor(audioProgress)}%)</span>
                                        <span style={{ color: '#ef4444' }}>{t('test.doNotRemoveHeadphones')}</span>
                                    </div>
                                    <div style={{ height: '8px', backgroundColor: '#e2e8f0', borderRadius: '9999px', overflow: 'hidden' }}>
                                        <div style={{ height: '100%', width: `${audioProgress}%`, backgroundColor: '#3b82f6', transition: 'width 1s linear' }}></div>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    <CardContent style={{ padding: '2rem', backgroundColor: '#fff' }}>

                        {phase === 'DIRECTIONS' && (
                            <div style={{ textAlign: 'center', padding: '2rem 0' }}>
                                <h2 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '1rem' }}>{t('test.directionsListening')}</h2>
                                <p style={{ color: '#475569', marginBottom: '2rem', maxWidth: '600px', margin: '0 auto 2rem', lineHeight: 1.6 }}>
                                    {t('test.listeningInstructions')}
                                </p>
                                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '1rem', marginBottom: '2rem' }}>
                                    <span style={{ fontSize: '1.25rem' }}>🔊</span>
                                    <input type="range" min="0" max="100" defaultValue="70" style={{ width: '200px' }} />
                                    <span style={{ fontSize: '0.875rem', color: '#64748b' }}>{t('test.testVolume')}</span>
                                </div>
                                <Button size="lg" onClick={handleStartAudio}>{t('test.beginLecture')}</Button>
                            </div>
                        )}

                        {phase === 'PLAYING_AUDIO' && (
                            <div style={{ textAlign: 'center', padding: '2rem 0' }}>
                                <h2 style={{ fontSize: '1.5rem', fontWeight: 600, color: '#f59e0b', marginBottom: '0.5rem' }}>{t('test.listenCarefully')}</h2>
                                <p style={{ color: '#475569' }}>{t('test.questionsAppearAuto')}</p>
                            </div>
                        )}

                        {phase === 'ANSWERING' && (
                            <div style={{ display: 'flex', flexDirection: 'column' }}>
                                <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1.5rem' }}>
                                    {currentQuestion === 1 && "What is the main topic of the lecture?"}
                                    {currentQuestion === 2 && "According to the professor, what was the primary cause of the economic shift in the region?"}
                                    {currentQuestion === 3 && "Why does the professor mention the 'trade routes'?"}
                                </h3>

                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '2rem' }}>
                                    <label style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1rem', border: '1px solid #e2e8f0', borderRadius: '8px', cursor: 'pointer', transition: 'background-color 0.2s' }}>
                                        <input type="radio" name={`q${currentQuestion}`} value="A" style={{ width: '1.25rem', height: '1.25rem' }} />
                                        <span style={{ fontSize: '1.125rem' }}>
                                            {currentQuestion === 1 && "The development of early agricultural tools."}
                                            {currentQuestion === 2 && "The introduction of new tax laws."}
                                            {currentQuestion === 3 && "To illustrate how ideas spread between distinct cultures."}
                                        </span>
                                    </label>
                                    <label style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1rem', border: '1px solid #e2e8f0', borderRadius: '8px', cursor: 'pointer', transition: 'background-color 0.2s' }}>
                                        <input type="radio" name={`q${currentQuestion}`} value="B" style={{ width: '1.25rem', height: '1.25rem' }} />
                                        <span style={{ fontSize: '1.125rem' }}>
                                            {currentQuestion === 1 && "The impact of climate migration on ancient trade networks."}
                                            {currentQuestion === 2 && "A sudden change in the local climate."}
                                            {currentQuestion === 3 && "To prove that the society was technologically advanced."}
                                        </span>
                                    </label>
                                    <label style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1rem', border: '1px solid #e2e8f0', borderRadius: '8px', cursor: 'pointer', transition: 'background-color 0.2s' }}>
                                        <input type="radio" name={`q${currentQuestion}`} value="C" style={{ width: '1.25rem', height: '1.25rem' }} />
                                        <span style={{ fontSize: '1.125rem' }}>
                                            {currentQuestion === 1 && "The political structure of the Bronze Age empires."}
                                            {currentQuestion === 2 && "Discoveries of precious metals nearby."}
                                            {currentQuestion === 3 && "To contrast them with modern transportation methods."}
                                        </span>
                                    </label>
                                    <label style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1rem', border: '1px solid #e2e8f0', borderRadius: '8px', cursor: 'pointer', transition: 'background-color 0.2s' }}>
                                        <input type="radio" name={`q${currentQuestion}`} value="D" style={{ width: '1.25rem', height: '1.25rem' }} />
                                        <span style={{ fontSize: '1.125rem' }}>
                                            {currentQuestion === 1 && "The architectural differences between two neighboring cities."}
                                            {currentQuestion === 2 && "The invention of standard coinage."}
                                            {currentQuestion === 3 && "To explain why they eventually collapsed."}
                                        </span>
                                    </label>
                                </div>

                                <div style={{ display: 'flex', justifyContent: 'flex-end', borderTop: '1px solid #e2e8f0', paddingTop: '1.5rem' }}>
                                    <Button onClick={handleNextQuestion}>
                                        {currentQuestion === totalQuestionsBlock1 ? t('test.submitAndEnterStage2') : t('test.next')}
                                    </Button>
                                </div>
                            </div>
                        )}

                    </CardContent>
                </Card>
            </main>
        </div>
    );
}
