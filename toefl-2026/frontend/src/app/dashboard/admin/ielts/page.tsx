'use client';

import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/Card';
import { Button } from '@/components/Button';
import { IeltsPreviewModal } from '@/components/IeltsPreviewModal';

// Static data extracted from DB for the dashboard
const stats = {
    totals: {
        passages: 129,
        groups: 362,
        questions: 1720
    },
    position: {
        "P1": 41,
        "P2": 38,
        "P3": 50
    },
    difficulty: {
        "unset": 44,
        "high": 53,
        "medium": 32
    },
    top10: [
        { "id": "ielts-r-105", "count": 16 },
        { "id": "ielts-r-085", "count": 14 },
        { "id": "ielts-r-074", "count": 14 },
        { "id": "ielts-r-118", "count": 14 },
        { "id": "ielts-r-064", "count": 14 },
        { "id": "ielts-r-065", "count": 14 },
        { "id": "ielts-r-078", "count": 14 },
        { "id": "ielts-r-099", "count": 14 },
        { "id": "ielts-r-084", "count": 14 },
        { "id": "ielts-r-109", "count": 14 }
    ]
};

export default function IeltsDashboard() {
    const [previewPassageId, setPreviewPassageId] = useState<string | null>(null);

    return (
        <div className="app-layout" style={{ backgroundColor: 'var(--background)' }}>
            <header style={{ padding: '1rem 2rem', borderBottom: '1px solid var(--border-color)', backgroundColor: 'var(--card-bg)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{ width: '32px', height: '32px', backgroundColor: '#3b82f6', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 'bold' }}>I</div>
                    <span style={{ fontWeight: 600, fontSize: '1.25rem' }}>IELTS Item Bank Dashboard</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <Button variant="ghost" size="sm" onClick={() => window.location.href = '/dashboard/admin'}>Back to Admin</Button>
                </div>
            </header>

            <main className="container" style={{ padding: '4rem 2rem', maxWidth: '1200px', margin: '0 auto' }}>
                <div style={{ marginBottom: '3rem' }}>
                    <h1 style={{ fontFamily: 'var(--font-heading)', fontSize: '2.5rem', marginBottom: '0.75rem', background: 'none', WebkitTextFillColor: 'var(--foreground)' }}>IELTS Reading Item Bank</h1>
                    <p style={{ color: 'var(--text-muted)' }}>Overview of all migrated reading passages, question groups, and individual questions.</p>
                </div>

                {/* Overview Stats */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem', marginBottom: '3rem' }}>
                    <Card style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--border-color)', boxShadow: 'none' }}>
                        <CardHeader style={{ paddingBottom: '0.5rem' }}>
                            <CardTitle style={{ fontFamily: 'var(--font-heading)', fontSize: '1.1rem', color: 'var(--text-muted)' }}>Total Passages</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div style={{ fontFamily: 'var(--font-heading)', fontSize: '3rem', fontWeight: 600 }}>{stats.totals.passages}</div>
                        </CardContent>
                    </Card>

                    <Card style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--border-color)', boxShadow: 'none' }}>
                        <CardHeader style={{ paddingBottom: '0.5rem' }}>
                            <CardTitle style={{ fontFamily: 'var(--font-heading)', fontSize: '1.1rem', color: 'var(--text-muted)' }}>Question Groups</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div style={{ fontFamily: 'var(--font-heading)', fontSize: '3rem', fontWeight: 600 }}>{stats.totals.groups}</div>
                        </CardContent>
                    </Card>

                    <Card style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--border-color)', boxShadow: 'none' }}>
                        <CardHeader style={{ paddingBottom: '0.5rem' }}>
                            <CardTitle style={{ fontFamily: 'var(--font-heading)', fontSize: '1.1rem', color: 'var(--text-muted)' }}>Total Questions</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div style={{ fontFamily: 'var(--font-heading)', fontSize: '3rem', fontWeight: 600 }}>{stats.totals.questions}</div>
                        </CardContent>
                    </Card>
                </div>

                {/* Detail Breakdowns */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '2.5rem' }}>
                    {/* By Position */}
                    <Card style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--border-color)', boxShadow: 'none' }}>
                        <CardHeader>
                            <CardTitle style={{ fontFamily: 'var(--font-heading)', fontSize: '1.25rem' }}>Passages by Position</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                                {Object.entries(stats.position).map(([pos, count]) => (
                                    <div key={pos} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                        <span style={{ fontWeight: 500 }}>Passage {pos.replace('P', '')}</span>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flex: 1, marginLeft: '1rem' }}>
                                            <div style={{ flex: 1, height: '8px', backgroundColor: 'var(--border-color)', borderRadius: '4px', overflow: 'hidden' }}>
                                                <div style={{ width: `${(count / stats.totals.passages) * 100}%`, height: '100%', backgroundColor: '#3b82f6' }} />
                                            </div>
                                            <span style={{ width: '40px', textAlign: 'right', color: 'var(--text-muted)' }}>{count}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>

                    {/* By Difficulty */}
                    <Card style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--border-color)', boxShadow: 'none' }}>
                        <CardHeader>
                            <CardTitle style={{ fontFamily: 'var(--font-heading)', fontSize: '1.25rem' }}>Passages by Difficulty</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                                {Object.entries(stats.difficulty).sort((a, b) => b[1] - a[1]).map(([diff, count]) => (
                                    <div key={diff} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                        <span style={{ fontWeight: 500, textTransform: 'capitalize' }}>{diff === 'unset' ? 'Unknown' : diff}</span>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flex: 1, marginLeft: '1rem' }}>
                                            <div style={{ flex: 1, height: '8px', backgroundColor: 'var(--border-color)', borderRadius: '4px', overflow: 'hidden' }}>
                                                <div style={{ width: `${(count / stats.totals.passages) * 100}%`, height: '100%', backgroundColor: diff === 'high' ? '#ef4444' : diff === 'medium' ? '#f59e0b' : '#94a3b8' }} />
                                            </div>
                                            <span style={{ width: '40px', textAlign: 'right', color: 'var(--text-muted)' }}>{count}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Top 10 Passages */}
                    <Card style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--border-color)', boxShadow: 'none', gridColumn: '1 / -1' }}>
                        <CardHeader>
                            <CardTitle style={{ fontFamily: 'var(--font-heading)', fontSize: '1.25rem' }}>Top 10 Longest Passages</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div style={{ overflowX: 'auto' }}>
                                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                                    <thead>
                                        <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                                            <th style={{ padding: '0.75rem 1rem', fontWeight: 500 }}>Passage ID</th>
                                            <th style={{ padding: '0.75rem 1rem', fontWeight: 500, textAlign: 'right' }}>Total Questions</th>
                                            <th style={{ padding: '0.75rem 1rem', fontWeight: 500, textAlign: 'right' }}>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {stats.top10.map((item, i) => (
                                            <tr key={item.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                                                <td style={{ padding: '0.75rem 1rem', fontWeight: 500 }}>{item.id}</td>
                                                <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>
                                                    <span style={{ display: 'inline-block', padding: '0.25rem 0.5rem', backgroundColor: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6', borderRadius: '4px', fontWeight: 600 }}>
                                                        {item.count}
                                                    </span>
                                                </td>
                                                <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>
                                                    <Button variant="ghost" size="sm" onClick={() => setPreviewPassageId(item.id)}>Preview</Button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </main >

            {/* Preview Modal */}
            < IeltsPreviewModal
                passageId={previewPassageId}
                onClose={() => setPreviewPassageId(null)
                }
            />
        </div >
    );
}
