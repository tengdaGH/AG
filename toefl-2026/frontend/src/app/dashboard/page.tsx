"use client";
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { API_BASE_URL } from '@/lib/api-config';

const THEME = {
    teal: '#006A70', tealDark: '#004d52', tealLight: '#e6f2f3',
    navy: '#1e293b', accent: '#f59e0b', success: '#10b981',
    bg: '#f8fafc', white: '#ffffff', text: '#334155'
};

export default function CommandCenter() {
    const [sessions, setSessions] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const router = useRouter();

    useEffect(() => {
        fetch(`${API_BASE_URL}/api/admin/sessions`)
            .then(res => res.json())
            .then(data => {
                setSessions(data);
                setLoading(false);
            })
            .catch(err => {
                console.error("Error fetching sessions:", err);
                setLoading(false);
            });
    }, []);

    return (
        <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
                <div>
                    <h1 style={{ color: THEME.navy, fontSize: 32, margin: '0 0 8px 0', fontWeight: 800 }}>Session Roster</h1>
                    <p style={{ color: '#64748b', margin: 0, fontSize: 16 }}>Overview of all recent testing sessions.</p>
                </div>
                <div style={{ background: THEME.white, padding: '12px 24px', borderRadius: 12, boxShadow: '0 4px 15px rgba(0,0,0,0.05)', color: THEME.text, fontWeight: 700, fontSize: 18, border: `1px solid #e2e8f0` }}>
                    <span style={{ color: THEME.teal, fontSize: 24, marginRight: 8 }}>{sessions.length}</span> Total Sessions
                </div>
            </div>

            <div style={{ background: THEME.white, borderRadius: 16, boxShadow: '0 10px 30px rgba(0,0,0,0.04)', overflow: 'hidden', border: '1px solid #e2e8f0' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                    <thead style={{ background: '#f1f5f9', borderBottom: '2px solid #e2e8f0' }}>
                        <tr>
                            <th style={{ padding: '20px 24px', fontWeight: 700, color: THEME.navy, textTransform: 'uppercase', fontSize: 12, letterSpacing: 1 }}>Candidate Details</th>
                            <th style={{ padding: '20px 24px', fontWeight: 700, color: THEME.navy, textTransform: 'uppercase', fontSize: 12, letterSpacing: 1 }}>Status</th>
                            <th style={{ padding: '20px 24px', fontWeight: 700, color: THEME.navy, textTransform: 'uppercase', fontSize: 12, letterSpacing: 1 }}>Started At</th>
                            <th style={{ padding: '20px 24px', fontWeight: 700, color: THEME.navy, textTransform: 'uppercase', fontSize: 12, letterSpacing: 1 }}>Total Score</th>
                            <th style={{ padding: '20px 24px', fontWeight: 700, color: THEME.navy, textTransform: 'uppercase', fontSize: 12, letterSpacing: 1, textAlign: 'right' }}>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr><td colSpan={5} style={{ padding: 40, textAlign: 'center', color: '#64748b', fontWeight: 600 }}>Loading sessions...</td></tr>
                        ) : sessions.length === 0 ? (
                            <tr><td colSpan={5} style={{ padding: 40, textAlign: 'center', color: '#64748b', fontWeight: 600 }}>No sessions found in the database.</td></tr>
                        ) : sessions.map((s: any, idx) => (
                            <tr key={s.id} style={{ borderBottom: '1px solid #f1f5f9', background: idx % 2 === 0 ? THEME.white : '#fafbfc', transition: 'background 0.2s' }}>
                                <td style={{ padding: '20px 24px' }}>
                                    <div style={{ color: THEME.navy, fontWeight: 700, fontSize: 16, marginBottom: 4 }}>{s.student_name}</div>
                                    <div style={{ fontSize: 13, color: '#94a3b8', fontFamily: 'monospace' }}>{s.student_id}</div>
                                </td>
                                <td style={{ padding: '20px 24px' }}>
                                    <span style={{
                                        padding: '6px 14px', borderRadius: 20, fontSize: 12, fontWeight: 700, letterSpacing: 0.5,
                                        background: s.status === 'COMPLETED' ? `${THEME.success}15` : (s.status === 'ACTIVE' ? `${THEME.teal}15` : `${THEME.accent}15`),
                                        color: s.status === 'COMPLETED' ? THEME.success : (s.status === 'ACTIVE' ? THEME.teal : THEME.accent)
                                    }}>
                                        {s.status}
                                    </span>
                                </td>
                                <td style={{ padding: '20px 24px', color: THEME.text, fontSize: 15 }}>
                                    {s.start_time ? new Date(s.start_time).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' }) : '—'}
                                </td>
                                <td style={{ padding: '20px 24px' }}>
                                    <span style={{ fontSize: 18, fontWeight: 800, color: s.total_score !== null ? THEME.navy : '#cbd5e1' }}>
                                        {s.total_score !== null ? s.total_score : 'Pending'}
                                    </span>
                                </td>
                                <td style={{ padding: '20px 24px', textAlign: 'right' }}>
                                    <button onClick={() => router.push(`/dashboard/${s.id}`)}
                                        style={{ padding: '10px 20px', background: THEME.teal, color: THEME.white, border: 'none', borderRadius: 8, fontWeight: 600, cursor: 'pointer', transition: 'all 0.2s', boxShadow: `0 4px 10px ${THEME.teal}40` }}
                                        onMouseEnter={e => { e.currentTarget.style.background = THEME.tealDark; e.currentTarget.style.transform = 'translateY(-2px)' }}
                                        onMouseLeave={e => { e.currentTarget.style.background = THEME.teal; e.currentTarget.style.transform = 'translateY(0)' }}
                                    >View Report</button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            <style>{`
                @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
            `}</style>
        </div>
    );
}
