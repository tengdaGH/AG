'use client';

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/Card';
import { Button } from '@/components/Button';
import { useLanguage } from '@/lib/i18n/LanguageContext';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';

export default function RaterDashboard() {
    const { t } = useLanguage();
    return (
        <div className="app-layout" style={{ backgroundColor: 'var(--background)' }}>
            <header style={{ padding: '1rem 2rem', borderBottom: '1px solid var(--border-color)', backgroundColor: 'var(--card-bg)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{ width: '32px', height: '32px', backgroundColor: '#8b5cf6', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 'bold' }}>R</div>
                    <span style={{ fontWeight: 600, fontSize: '1.25rem' }}>{t('rater.portal')}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <LanguageSwitcher />
                    <span style={{ color: 'var(--text-muted)' }}>{t('rater.expertRater')}</span>
                    <Button variant="ghost" size="sm" onClick={() => window.location.href = '/'}>{t('rater.signOut')}</Button>
                </div>
            </header>

            <main className="container" style={{ paddingTop: '2rem', paddingBottom: '2rem' }}>
                <div style={{ marginBottom: '2rem' }}>
                    <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem', background: 'none', WebkitTextFillColor: 'var(--foreground)' }}>{t('rater.queue')}</h1>
                    <p style={{ color: 'var(--text-muted)' }}>{t('rater.queueDesc')}</p>
                </div>

                <div className="grid-cards">
                    <Card>
                        <CardHeader>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                <CardTitle>{t('rater.speakingResponses')}</CardTitle>
                                <span style={{ padding: '0.25rem 0.75rem', backgroundColor: '#fee2e2', color: '#b91c1c', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 600 }}>{t('rater.speakingPending')}</span>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>{t('rater.speakingDesc')}</p>
                            <Button fullWidth>{t('rater.startQueue')}</Button>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                <CardTitle>{t('rater.writingResponses')}</CardTitle>
                                <span style={{ padding: '0.25rem 0.75rem', backgroundColor: '#fef3c7', color: '#b45309', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 600 }}>{t('rater.writingPending')}</span>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>{t('rater.writingDesc')}</p>
                            <Button variant="secondary" fullWidth>{t('rater.reviewEssays')}</Button>
                        </CardContent>
                    </Card>
                </div>
            </main>
        </div>
    );
}
