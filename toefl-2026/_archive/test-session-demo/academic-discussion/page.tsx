'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { TestTimer } from '@/components/TestTimer';
import { Button } from '@/components/Button';
import { WriteAcademicDiscussion } from '@/components/WriteAcademicDiscussion';
import { useLanguage } from '@/lib/i18n/LanguageContext';

export default function WriteAcademicDiscussionTask() {
    const router = useRouter();
    const { t } = useLanguage();
    const [emailBody, setEmailBody] = useState('');
    const [wordCount, setWordCount] = useState(0);
    const [isScoring, setIsScoring] = useState(false);

    useEffect(() => {
        const words = emailBody.trim().split(/\s+/);
        setWordCount(emailBody.trim() === '' ? 0 : words.length);
    }, [emailBody]);

    const handleNext = async () => {
        if (wordCount < 100) {
            const confirmSubmit = window.confirm(t('test.underWordCountWarning') || 'You are under the word count. Submit anyway?');
            if (!confirmSubmit) return;
        }

        setIsScoring(true);
        // fake scoring for sandbox
        await new Promise(resolve => setTimeout(resolve, 1000));
        setIsScoring(false);

        alert(`Task Completed! Scoring would happen here.`);
        router.push('/dashboard/student');
    };

    const handleTimeUp = async () => {
        setIsScoring(true);
        await new Promise(resolve => setTimeout(resolve, 1000));
        setIsScoring(false);

        alert(`Time's up! Task Completed!`);
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
                        Writing Section: Academic Discussion
                    </div>
                </div>

                {/* 10 minutes for the task */}
                <TestTimer fallbackSeconds={600} onTimeUp={handleTimeUp} sectionName="Time Remaining" />

                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{ fontSize: '0.875rem', color: '#cbd5e1' }}>Task 2 of 2</div>
                    <div title="Stable Connection" style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#22c55e' }}></div>
                </div>
            </header>

            <main style={{ flex: 1, padding: '2rem', display: 'flex', flexDirection: 'column', maxWidth: '1400px', margin: '0 auto', width: '100%' }}>
                <div style={{ flex: 1, minHeight: '600px' }}>
                    <WriteAcademicDiscussion
                        professorAvatarUrl="/avatars/professor.jpg"
                        professorPromptHTML={`<p>Let's discuss the skills most needed by people who want to start and run their own business. Some experts propose that future businesspeople should focus on improving their sales techniques —after all, if you cannot sell your product, you will soon be out of business. Others believe that these future businesspeople would benefit most from learning management skills, such as how to lead teams and motivate employees. Which view do you agree with? Why?</p>`}
                        studentPosts={[
                            {
                                id: '1',
                                authorName: 'Andrew',
                                avatarUrl: '/avatars/andrew.jpg',
                                text: 'I think that management skills are most important. Sales tasks are something that a businessperson can delegate to a team of salespeople once the business gets going, so it is really important that the future businessperson develops skills to manage teams of people. Without that, it is not very likely that the business will grow.'
                            },
                            {
                                id: '2',
                                authorName: 'Kelly',
                                avatarUrl: '/avatars/kelly.jpg',
                                text: "Learning how to sell your product is the most essential task. I've read about people who had ideas about exciting new products to build a business around. They borrowed capital and started their business, but they could not explain to the public what made the products exciting. Since they could not sell enough products, their business failed."
                            }
                        ]}
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
