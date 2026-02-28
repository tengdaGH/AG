'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/Card';
import { Input } from '@/components/Input';
import { Button } from '@/components/Button';
import { useLanguage } from '@/lib/i18n/LanguageContext';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';
import { API_BASE_URL } from '@/lib/api-config';

export default function LoginPage() {
    const router = useRouter();
    const { t } = useLanguage();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [role, setRole] = useState('STUDENT');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        if (role === 'STUDENT') {
            try {
                const response = await fetch(`${API_BASE_URL}/api/auth/student-login`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Bypass-Tunnel-Reminder': 'true'
                    },
                    body: JSON.stringify({
                        student_id: email,
                        password: password,
                    }),
                });

                if (!response.ok) {
                    const data = await response.json();
                    throw new Error(data.detail || 'Login failed');
                }

                const userData = await response.json();

                // Save user data to localStorage so test components can retrieve their actual ID
                localStorage.setItem('student_id', userData.student_id);
                localStorage.setItem('user_id', userData.user_id);

                router.push('/dashboard/student');
            } catch (err: any) {
                setError(err.message || 'Authentication error');
            } finally {
                setLoading(false);
            }
        } else {
            // Mock other roles since they aren't critical right now based on user feedback
            setTimeout(() => {
                setLoading(false);
                switch (role) {
                    case 'ADMIN':
                        router.push('/dashboard/admin');
                        break;
                    case 'RATER':
                        router.push('/dashboard/rater');
                        break;
                    case 'PROCTOR':
                        router.push('/dashboard/proctor');
                        break;
                    default:
                        router.push('/');
                }
            }, 800);
        }
    };

    return (
        <div className="app-layout" style={{ backgroundColor: 'var(--background)', minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem', position: 'relative' }}>
            <div style={{ position: 'absolute', top: '2rem', right: '2rem' }}>
                <LanguageSwitcher />
            </div>
            <main style={{ width: '100%', maxWidth: '420px' }}>
                <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                    <div style={{ display: 'inline-flex', width: '48px', height: '48px', backgroundColor: 'var(--primary-blue)', borderRadius: '12px', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 'bold', fontSize: '1.5rem', marginBottom: '1rem' }}>
                        T
                    </div>
                    <h1 style={{ fontSize: '1.75rem', marginBottom: '0.5rem', background: 'none', WebkitTextFillColor: 'var(--foreground)' }}>
                        {t('login.welcome')}
                    </h1>
                    <p style={{ color: 'var(--text-muted)' }}>{t('login.subtitle')}</p>
                </div>

                <Card>
                    <form onSubmit={handleLogin}>
                        <CardHeader>
                            <CardTitle>{t('login.signInBtn')}</CardTitle>
                        </CardHeader>
                        {error && (
                            <div style={{ margin: '0 1.5rem', padding: '0.75rem', backgroundColor: '#fee2e2', color: '#b91c1c', borderRadius: '6px', fontSize: '0.875rem' }}>
                                {error}
                            </div>
                        )}
                        <CardContent>
                            <Input
                                id="email"
                                type="text"
                                label={t('login.email')}
                                placeholder="name@example.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                            />
                            <Input
                                id="password"
                                type="password"
                                label={t('login.password')}
                                placeholder="••••••••"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                            />

                            <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
                                <label style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--foreground)' }}>
                                    {t('login.roleLabel')}
                                </label>
                                <select
                                    value={role}
                                    onChange={(e) => setRole(e.target.value)}
                                    style={{
                                        height: '2.5rem',
                                        width: '100%',
                                        borderRadius: '6px',
                                        border: '1px solid var(--border-color)',
                                        backgroundColor: 'var(--card-bg)',
                                        padding: '0 0.75rem',
                                        fontSize: '1rem',
                                        color: 'var(--foreground)',
                                        outline: 'none',
                                        fontFamily: 'inherit'
                                    }}
                                >
                                    <option value="STUDENT">{t('login.roleStudent')}</option>
                                    <option value="ADMIN">{t('login.roleAdmin')}</option>
                                    <option value="RATER">{t('login.roleRater')}</option>
                                    <option value="PROCTOR">{t('login.roleProctor')}</option>
                                </select>
                            </div>
                        </CardContent>
                        <CardFooter style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                            <Button type="submit" fullWidth disabled={loading}>
                                {loading ? t('login.authenticating') : t('login.signInBtn')}
                            </Button>
                            <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', textAlign: 'center' }}>
                                {t('login.noAccount')} <a href="#" style={{ color: 'var(--primary-blue)', textDecoration: 'none', fontWeight: 500 }}>{t('login.createAccount')}</a>
                            </div>
                        </CardFooter>
                    </form>
                </Card>
            </main>
        </div>
    );
}
