'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { TestTimer } from '@/components/TestTimer';
import { useLanguage } from '@/lib/i18n/LanguageContext';
import { ReadingPassage } from '@/components/ReadingPassage';
import { ReadingQuestion } from '@/components/ReadingQuestion';

interface Question {
    question_num: number;
    text: string;
    options: string[];
    correct_answer: number;
}

interface TestItem {
    id: string;
    section: string;
    prompt_content: string;
    is_active: boolean;
}

import { normaliseContent } from '@/lib/content-utils';
import { API_BASE_URL } from '@/lib/api-config';

export default function DemoTestSession() {
    const router = useRouter();
    const { t } = useLanguage();
    const [loading, setLoading] = useState(true);
    const [items, setItems] = useState<any[]>([]);
    const [currentItemIndex, setCurrentItemIndex] = useState(0);
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [answers, setAnswers] = useState<Record<string, Record<number, number>>>({});

    useEffect(() => {
        const fetchItems = async () => {
            try {
                const res = await fetch(`${API_BASE_URL}/api/items`, {
                    headers: {
                        'Bypass-Tunnel-Reminder': 'true'
                    }
                });
                if (res.ok) {
                    const data: TestItem[] = await res.json();

                    // Normalise all active reading items
                    const readingItems = data
                        .filter(item => item.section === 'READING' && item.is_active)
                        .map(item => {
                            const raw = JSON.parse(item.prompt_content);
                            return {
                                ...item,
                                parsedContent: normaliseContent(raw, item)
                            };
                        });

                    // Prioritize C-test if available for demonstration
                    const ctestItems = readingItems.filter(item => item.parsedContent.type.includes('Complete'));
                    const otherItems = readingItems.filter(item => !item.parsedContent.type.includes('Complete'));

                    setItems([...ctestItems, ...otherItems].slice(0, 3));
                }
            } catch (error) {
                console.error('Failed to fetch items:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchItems();
    }, []);


    const currentItem = items[currentItemIndex];
    const totalQuestions = currentItem?.parsedContent?.questions?.length || 0;

    const handleNext = () => {
        if (currentQuestionIndex < totalQuestions - 1) {
            setCurrentQuestionIndex(curr => curr + 1);
        } else if (currentItemIndex < items.length - 1) {
            setCurrentItemIndex(curr => curr + 1);
            setCurrentQuestionIndex(0);
        } else {
            // Move to next section
            alert(t('test.readingCompleteAlert'));
            router.push('/test-session/demo/listening');
        }
    };

    const handleBack = () => {
        if (currentQuestionIndex > 0) {
            setCurrentQuestionIndex(curr => curr - 1);
        } else if (currentItemIndex > 0) {
            setCurrentItemIndex(curr => curr - 1);
            const prevItem = items[currentItemIndex - 1];
            setCurrentQuestionIndex((prevItem?.parsedContent?.questions?.length || 1) - 1);
        }
    };

    const handleAnswerChange = (questionNum: number, answerIndex: number) => {
        setAnswers(prev => ({
            ...prev,
            [currentItem.id]: {
                ...(prev[currentItem.id] || {}),
                [questionNum]: answerIndex
            }
        }));
    };

    const handleTimeUp = () => {
        alert(t('test.timeUpAlert'));
        router.push('/dashboard/student');
    };

    if (loading) {
        return <div style={{ display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center' }}>Loading Reading Section...</div>;
    }

    if (items.length === 0) {
        return <div style={{ display: 'flex', height: '100vh', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '1rem' }}>
            <p>No reading items found in the database.</p>
            <button onClick={() => router.push('/dashboard/student')}>Return to Dashboard</button>
        </div>;
    }

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', backgroundColor: '#f8fafc' }}>
            {/* Test Header */}
            <header style={{
                backgroundColor: '#1e293b',
                color: 'white',
                padding: '0.75rem 2rem',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                zIndex: 10
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                    <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>TOEFL iBT</div>
                    <div style={{ padding: '0.25rem 0.75rem', backgroundColor: '#334155', borderRadius: '4px', fontSize: '0.875rem' }}>
                        {t('test.readingSection')}
                    </div>
                    <div style={{ fontSize: '0.875rem', color: '#94a3b8' }}>
                        {currentItem?.parsedContent?.type}
                    </div>
                </div>

                <TestTimer initialSeconds={currentItem?.parsedContent?.type.includes('Complete') ? 600 : 2100} onTimeUp={handleTimeUp} sectionName={t('test.timeRemaining')} />

                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{ fontSize: '0.875rem', color: '#cbd5e1' }}>
                        {t('test.question')} {currentQuestionIndex + 1} / {totalQuestions}
                    </div>
                    <div title={t('test.connectionStable')} style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#22c55e' }}></div>
                </div>
            </header>

            {/* Test Content Area */}
            <main style={{ flex: 1, padding: '2rem', display: 'flex', gap: '2rem', maxWidth: '1600px', margin: '0 auto', width: '100%', overflow: 'hidden' }}>
                <ReadingPassage
                    type={currentItem.parsedContent.type}
                    title={currentItem.parsedContent.title}
                    text={currentItem.parsedContent.text}
                    currentQuestionIndex={currentQuestionIndex}
                    onAnswerChange={handleAnswerChange}
                    answers={answers[currentItem.id] || {}}
                />

                <ReadingQuestion
                    questions={currentItem.parsedContent.questions}
                    currentQuestionIndex={currentQuestionIndex}
                    totalQuestions={totalQuestions}
                    onNext={handleNext}
                    onBack={handleBack}
                    onAnswerChange={handleAnswerChange}
                    answers={answers[currentItem.id] || {}}
                    submitLabel={currentItemIndex === items.length - 1 ? t('test.submitSection') : t('test.next')}
                    nextLabel={t('test.next')}
                    backLabel={t('test.back')}
                />
            </main>
        </div>
    );
}
