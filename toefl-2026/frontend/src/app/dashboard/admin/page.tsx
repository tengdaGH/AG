'use client';

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/Card';
import { Button } from '@/components/Button';
import { useLanguage } from '@/lib/i18n/LanguageContext';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';

export default function AdminDashboard() {
    const { t } = useLanguage();
    return (
        <div className="app-layout" style={{ backgroundColor: 'var(--background)' }}>
            <header style={{ padding: '1rem 2rem', borderBottom: '1px solid var(--border-color)', backgroundColor: 'var(--card-bg)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{ width: '32px', height: '32px', backgroundColor: '#ef4444', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 'bold' }}>A</div>
                    <span style={{ fontWeight: 600, fontSize: '1.25rem' }}>{t('admin.portal')}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <LanguageSwitcher />
                    <span style={{ color: 'var(--text-muted)' }}>Admin User</span>
                    <Button variant="ghost" size="sm" onClick={() => window.location.href = '/'}>{t('admin.signOut')}</Button>
                </div>
            </header>

            <main className="container" style={{ padding: '4rem 2rem', maxWidth: '1000px', margin: '0 auto' }}>
                <div style={{ marginBottom: '3rem' }}>
                    <h1 style={{ fontFamily: 'var(--font-heading)', fontSize: '2.5rem', marginBottom: '0.75rem', background: 'none', WebkitTextFillColor: 'var(--foreground)' }}>{t('admin.overview')}</h1>
                </div>

                <div className="grid-cards" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '2.5rem' }}>
                    <Card style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--border-color)', boxShadow: 'none' }}>
                        <CardHeader style={{ paddingBottom: '0.5rem' }}>
                            <CardTitle style={{ fontFamily: 'var(--font-heading)', fontSize: '1.25rem' }}>{t('admin.manageItemsTitle')}</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div style={{ fontFamily: 'var(--font-body)', fontSize: '3rem', fontWeight: 500, marginBottom: '1rem', color: 'var(--foreground)' }}>1,432</div>
                            <p style={{ fontFamily: 'var(--font-body)', color: 'var(--text-muted)', marginBottom: '2rem', fontSize: '1.1rem' }}>{t('admin.manageItemsDesc')}</p>
                            <div style={{ display: 'flex', gap: '1rem' }}>
                                <Button fullWidth onClick={() => window.location.href = '/dashboard/admin/items'} style={{ backgroundColor: 'var(--foreground)', color: 'var(--background)' }}>{t('admin.manageItemsBtn')}</Button>
                                <Button variant="secondary" fullWidth style={{ border: '1px solid var(--border-color)' }}>{t('admin.createNewBtn')}</Button>
                            </div>
                        </CardContent>
                    </Card>

                    <Card style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--border-color)', boxShadow: 'none' }}>
                        <CardHeader style={{ paddingBottom: '0.5rem' }}>
                            <CardTitle style={{ fontFamily: 'var(--font-heading)', fontSize: '1.25rem' }}>{t('admin.systemHealthTitle')}</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', fontFamily: 'var(--font-body)' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '0.75rem', borderBottom: '1px solid var(--border-color)' }}>
                                    <span style={{ color: 'var(--text-muted)' }}>{t('admin.dbOnline')}</span>
                                    <span style={{ color: '#16a34a', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.9rem' }}>
                                        <div style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#16a34a' }}></div>
                                        {t('admin.statusOnline')}
                                    </span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '0.75rem', borderBottom: '1px solid var(--border-color)' }}>
                                    <span style={{ color: 'var(--text-muted)' }}>{t('admin.aiOnline')}</span>
                                    <span style={{ color: '#16a34a', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.9rem' }}>
                                        <div style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#16a34a' }}></div>
                                        {t('admin.statusOnline')}
                                    </span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <span style={{ color: 'var(--text-muted)' }}>{t('admin.webrtcStatus')}</span>
                                    <span style={{ color: '#d97757', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.9rem' }}>
                                        <div style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#d97757' }}></div>
                                        {t('admin.statusDegraded')}
                                    </span>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    <Card style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--border-color)', boxShadow: 'none' }}>
                        <CardHeader style={{ paddingBottom: '0.5rem' }}>
                            <CardTitle style={{ fontFamily: 'var(--font-heading)', fontSize: '1.25rem' }}>IELTS Item Bank</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p style={{ fontFamily: 'var(--font-body)', color: 'var(--text-muted)', marginBottom: '2rem', fontSize: '1.1rem' }}>Manage the migrated IELTS Reading passages and questions. View item bank statistics and health.</p>
                            <Button variant="secondary" fullWidth onClick={() => window.location.href = '/dashboard/admin/ielts'} style={{ border: '1px solid var(--border-color)' }}>View Dashboard</Button>
                        </CardContent>
                    </Card>

                    <Card style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--border-color)', boxShadow: 'none' }}>
                        <CardHeader style={{ paddingBottom: '0.5rem' }}>
                            <CardTitle style={{ fontFamily: 'var(--font-heading)', fontSize: '1.25rem' }}>{t('admin.userMgmtTitle')}</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p style={{ fontFamily: 'var(--font-body)', color: 'var(--text-muted)', marginBottom: '2rem', fontSize: '1.1rem' }}>{t('admin.userMgmtDesc')}</p>
                            <Button variant="secondary" fullWidth style={{ border: '1px solid var(--border-color)' }}>{t('admin.viewDirectoryBtn')}</Button>
                        </CardContent>
                    </Card>
                </div>
            </main>
        </div>
    );
}
