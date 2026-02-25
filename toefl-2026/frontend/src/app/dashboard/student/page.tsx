'use client';

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/Card';
import { Button } from '@/components/Button';
import { useLanguage } from '@/lib/i18n/LanguageContext';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';

export default function StudentDashboard() {
    const { t } = useLanguage();
    return (
        <div className="app-layout" style={{ backgroundColor: 'var(--background)' }}>
            <header style={{ padding: '1rem 2rem', borderBottom: '1px solid var(--border-color)', backgroundColor: 'var(--card-bg)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{ width: '32px', height: '32px', backgroundColor: 'var(--primary-blue)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 'bold' }}>T</div>
                    <span style={{ fontWeight: 600, fontSize: '1.25rem' }}>{t('student.portal')}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <LanguageSwitcher />
                    <span style={{ color: 'var(--text-muted)' }}>Jane Doe (ID: 98765432)</span>
                    <Button variant="ghost" size="sm" onClick={() => window.location.href = '/'}>{t('student.signOut')}</Button>
                </div>
            </header>

            <main className="container" style={{ paddingTop: '2rem', paddingBottom: '2rem' }}>
                <div style={{ marginBottom: '2rem' }}>
                    <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem', background: 'none', WebkitTextFillColor: 'var(--foreground)' }}>{t('student.myAssessments')}</h1>
                    <p style={{ color: 'var(--text-muted)' }}>{t('student.myAssessmentsDesc')}</p>
                </div>

                <div className="grid-cards">
                    <Card>
                        <CardHeader>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                <CardTitle>{t('student.simulation')}</CardTitle>
                                <span style={{ padding: '0.25rem 0.75rem', backgroundColor: '#e0e7ff', color: '#4338ca', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 600 }}>{t('student.upcoming')}</span>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <p style={{ marginBottom: '1rem' }}>{t('student.testDate')}: <strong>May 15, 2026</strong> • 9:00 AM EST</p>
                            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginBottom: '1.5rem' }}>
                                {t('student.testDateDesc')}
                            </p>
                            <Button fullWidth onClick={() => window.location.href = '/test-session/demo'}>{t('student.launchProctor')}</Button>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                <CardTitle>{t('student.speakingPractice')}</CardTitle>
                                <span style={{ padding: '0.25rem 0.75rem', backgroundColor: '#dcfce7', color: '#166534', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 600 }}>{t('student.practice')}</span>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <p style={{ marginBottom: '1rem' }}>{t('student.topic')}</p>
                            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginBottom: '1.5rem' }}>
                                {t('student.practiceDesc')}
                            </p>
                            <Button variant="secondary" fullWidth>{t('student.startPractice')}</Button>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle>{t('student.pastScores')}</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '0.5rem', borderBottom: '1px solid var(--border-color)' }}>
                                    <span>{t('student.diagnosticTest')}</span>
                                    <span style={{ fontWeight: 600 }}>{t('student.totalScore')}: 105/120</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '0.5rem', borderBottom: '1px solid var(--border-color)' }}>
                                    <span>{t('student.writingOnly')}</span>
                                    <span style={{ fontWeight: 600 }}>24/30</span>
                                </div>
                            </div>
                            <Button variant="ghost" fullWidth style={{ marginTop: '1rem' }}>{t('student.viewAnalytics')}</Button>
                        </CardContent>
                    </Card>
                </div>
            </main>
        </div>
    );
}
