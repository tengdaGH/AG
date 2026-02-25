'use client';

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/Card';
import { Button } from '@/components/Button';
import { useLanguage } from '@/lib/i18n/LanguageContext';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';

export default function ProctorDashboard() {
    const { t } = useLanguage();
    return (
        <div className="app-layout" style={{ backgroundColor: 'var(--background)' }}>
            <header style={{ padding: '1rem 2rem', borderBottom: '1px solid var(--border-color)', backgroundColor: 'var(--card-bg)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{ width: '32px', height: '32px', backgroundColor: '#0ea5e9', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 'bold' }}>P</div>
                    <span style={{ fontWeight: 600, fontSize: '1.25rem' }}>{t('proctor.portal')}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <LanguageSwitcher />
                    <span style={{ color: 'var(--text-muted)' }}>{t('proctor.activeSession')}</span>
                    <Button variant="ghost" size="sm" onClick={() => window.location.href = '/'}>{t('proctor.endSession')}</Button>
                </div>
            </header>

            <main className="container" style={{ paddingTop: '2rem', paddingBottom: '2rem' }}>
                <div style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
                    <div>
                        <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem', background: 'none', WebkitTextFillColor: 'var(--foreground)' }}>{t('proctor.testCenter')}</h1>
                        <p style={{ color: 'var(--text-muted)' }}>{t('proctor.monitoring')}</p>
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <Button variant="danger">{t('proctor.lockdownAll')}</Button>
                    </div>
                </div>

                <div className="grid-cards">
                    <Card>
                        <CardHeader>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                <CardTitle>{t('proctor.station04')}</CardTitle>
                                <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#ef4444' }}></div>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <p style={{ fontWeight: 600, marginBottom: '0.25rem' }}>{t('proctor.candidate948112')}</p>
                            <p style={{ color: '#ef4444', fontSize: '0.875rem', marginBottom: '1rem' }}>{t('proctor.aiFlag')}</p>
                            <div style={{ display: 'flex', gap: '0.5rem' }}>
                                <Button size="sm" fullWidth>{t('proctor.viewStream')}</Button>
                                <Button size="sm" variant="secondary" fullWidth>{t('proctor.pauseExam')}</Button>
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                <CardTitle>{t('proctor.station12')}</CardTitle>
                                <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#16a34a' }}></div>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <p style={{ fontWeight: 600, marginBottom: '0.25rem' }}>{t('proctor.candidate991244')}</p>
                            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginBottom: '1rem' }}>{t('proctor.listening')}</p>
                            <div style={{ display: 'flex', gap: '0.5rem' }}>
                                <Button size="sm" variant="secondary" fullWidth>{t('proctor.viewStream')}</Button>
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                <CardTitle>{t('proctor.station15')}</CardTitle>
                                <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#16a34a' }}></div>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <p style={{ fontWeight: 600, marginBottom: '0.25rem' }}>{t('proctor.candidate991288')}</p>
                            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginBottom: '1rem' }}>{t('proctor.reading')}</p>
                            <div style={{ display: 'flex', gap: '0.5rem' }}>
                                <Button size="sm" variant="secondary" fullWidth>{t('proctor.viewStream')}</Button>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </main>
        </div>
    );
}
