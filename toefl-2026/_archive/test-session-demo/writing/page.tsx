'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { TestTimer } from '@/components/TestTimer';
import { Button } from '@/components/Button';
import { WriteEmail } from '@/components/WriteEmail';
import { evaluateWritingResponse } from '@/lib/scoring-engine/ai-scorer';
import { useLanguage } from '@/lib/i18n/LanguageContext';

export default function WriteAnEmailTask() {
    const router = useRouter();
    const { t } = useLanguage();
    const [emailBody, setEmailBody] = useState('');
    const [wordCount, setWordCount] = useState(0);
    const [isScoring, setIsScoring] = useState(false);

    // CJK-aware word count: for scripts without spaces, count characters
    useEffect(() => {
        const trimmed = emailBody.trim();
        if (trimmed === '') { setWordCount(0); return; }
        // Check if text contains CJK characters
        const cjkChars = trimmed.match(/[\u4e00-\u9fff\u3400-\u4dbf\uac00-\ud7af\u3040-\u309f\u30a0-\u30ff]/g);
        if (cjkChars && cjkChars.length > trimmed.split(/\s+/).length) {
            // CJK: count characters (roughly 1 word per 1.5 chars)
            setWordCount(Math.ceil(cjkChars.length / 1.5));
        } else {
            setWordCount(trimmed.split(/\s+/).length);
        }
    }, [emailBody]);

    const handleNext = async () => {
        setIsScoring(true);
        try {
            const score = await evaluateWritingResponse(emailBody, 50);
            // Navigate immediately — don't block with alert
            router.push('/dashboard/student');
        } catch {
            router.push('/dashboard/student');
        }
    };

    const handleTimeUp = async () => {
        setIsScoring(true);
        try {
            await evaluateWritingResponse(emailBody, 50);
        } catch { }
        router.push('/dashboard/student');
    };

    return (
        <>
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
                        {t('test.writingSectionEmail')}
                    </div>
                </div>

                {/* 10 minutes for the new 'Write an Email' task */}
                <TestTimer fallbackSeconds={600} onTimeUp={handleTimeUp} sectionName={t('test.timeRemaining')} />

                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{ fontSize: '0.875rem', color: '#cbd5e1' }}>{t('test.task1Of2')}</div>
                    <div title={t('test.connectionStable')} style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#22c55e' }}></div>
                </div>
            </header>

            <main style={{ flex: 1, padding: '2rem', display: 'flex', flexDirection: 'column', maxWidth: '1400px', margin: '0 auto', width: '100%' }}>
                <div style={{ flex: 1, minHeight: '600px' }}>
                    <WriteEmail
                        promptHTML={`
                            <div style="font-family: 'Times New Roman', Times, serif; font-size: 16px; color: #000; line-height: 1.4;">
                                <p style="margin-top: 0;">${t('test.scenarioBody')}</p>
                                <p><strong>${t('test.taskBody')}</strong></p>
                                <ul style="padding-left: 20px; margin-top: 10px; margin-bottom: 20px;">
                                    <li style="margin-bottom: 5px; list-style-type: disc;">${t('test.taskBullet1')}</li>
                                    <li style="margin-bottom: 5px; list-style-type: disc;">${t('test.taskBullet2')}</li>
                                    <li style="margin-bottom: 5px; list-style-type: disc;">${t('test.taskBullet3')}</li>
                                </ul>
                                <p>Write as much as you can and in complete sentences.</p>
                            </div>
                        `}
                        emailTo="editor@sunshinepoetrymagazine.com"
                        emailSubject="Problem using submission form"
                        onSave={(content: string) => setEmailBody(content)}
                    />
                </div>

                <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'flex-end' }}>
                    <Button onClick={handleNext} disabled={isScoring}>
                        {isScoring ? t('test.analyzingSubmissions') : t('test.submitResponse')}
                    </Button>
                </div>
            </main>
        </>
    );
}
