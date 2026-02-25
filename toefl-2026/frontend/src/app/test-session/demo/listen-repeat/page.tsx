'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { TestTimer } from '@/components/TestTimer';
import { Button } from '@/components/Button';
import { ListenRepeat } from '@/components/ListenRepeat';
import { useLanguage } from '@/lib/i18n/LanguageContext';

export default function ListenRepeatTask() {
    const router = useRouter();
    const { t } = useLanguage();
    const [isScoring, setIsScoring] = useState(false);

    const handleNext = async () => {
        setIsScoring(true);
        // fake transition
        await new Promise(resolve => setTimeout(resolve, 800));
        setIsScoring(false);

        alert(`Task Completed! Scoring would happen here.`);
        router.push('/dashboard/student');
    };

    const handleTimeUp = async () => {
        setIsScoring(true);
        await new Promise(resolve => setTimeout(resolve, 800));
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
                        Speaking Section: Listen and Repeat
                    </div>
                </div>

                {/* Typically minimal time for these rapid fire items */}
                <TestTimer initialSeconds={60} onTimeUp={handleTimeUp} sectionName="Time Remaining" />

                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{ fontSize: '0.875rem', color: '#cbd5e1' }}>Task 4 of 6</div>
                    <div title="Stable Connection" style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#22c55e' }}></div>
                </div>
            </header>

            <main style={{ flex: 1, padding: '2rem', display: 'flex', flexDirection: 'column', maxWidth: '1200px', margin: '0 auto', width: '100%' }}>

                {/* The main container taking up the bulk of the screen */}
                <div style={{ flex: 1, minHeight: '500px' }}>
                    <ListenRepeat
                        imageUrl="/images/listen_repeat_zoo_sample.jpg"
                        imageAlt="A group of people looking at animals in a zoo enclosure"
                    />
                </div>

                <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'flex-end' }}>
                    <Button onClick={handleNext} disabled={isScoring}>
                        {isScoring ? t('test.analyzingSubmissions') || 'Processing...' : 'Next'}
                    </Button>
                </div>
            </main>
        </>
    );
}
