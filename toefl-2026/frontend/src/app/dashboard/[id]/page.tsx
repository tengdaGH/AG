"use client";
import React, { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { API_BASE_URL } from '@/lib/api-config';
import { ArrowLeft, Clock, AlertTriangle, ShieldCheck, FileText, Mic, CheckCircle, XCircle, BrainCircuit } from 'lucide-react';

const THEME = {
    teal: '#006A70', tealDark: '#004d52', tealLight: '#e6f2f3',
    navy: '#1e293b', accent: '#f59e0b', success: '#10b981', error: '#ef4444',
    bg: '#f8fafc', white: '#ffffff', text: '#334155'
};

export default function CandidateReport() {
    const params = useParams();
    const router = useRouter();
    const [data, setData] = useState<any>(null);
    const [logs, setLogs] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        Promise.all([
            fetch(`${API_BASE_URL}/api/admin/sessions/${params.id}`).then(res => res.json()),
            fetch(`${API_BASE_URL}/api/admin/sessions/${params.id}/logs`).then(res => res.json())
        ]).then(([sessionRes, logsRes]) => {
            setData(sessionRes);
            setLogs(logsRes);
            setLoading(false);
        }).catch(err => {
            console.error(err);
            setLoading(false);
        });
    }, [params.id]);

    if (loading) {
        return <div style={{ padding: 40, textAlign: 'center', color: THEME.text }}>Loading report...</div>;
    }

    if (!data || !data.session) {
        return <div style={{ padding: 40, textAlign: 'center', color: THEME.error }}>Report not found.</div>;
    }

    const { session, responses } = data;

    // Calculate Scores per Section
    const scoreMap = {
        READING: { correct: 0, total: 0 },
        LISTENING: { correct: 0, total: 0 },
        SPEAKING: { crGiven: 0, maxScore: 0, responses: [] as any[] },
        WRITING: { crGiven: 0, maxScore: 0, responses: [] as any[] },
        UNKNOWN: { correct: 0, total: 0 }
    };

    responses.forEach((r: any) => {
        const sec = (r.section || 'UNKNOWN').toUpperCase() as keyof typeof scoreMap;
        if (sec === 'READING' || sec === 'LISTENING') {
            (scoreMap[sec] as any).total += 1;
            if (r.is_correct) (scoreMap[sec] as any).correct += 1;
        } else if (sec === 'SPEAKING' || sec === 'WRITING') {
            if (r.rubric_score !== null) {
                (scoreMap[sec] as any).crGiven += Number(r.rubric_score);
                (scoreMap[sec] as any).maxScore += Number(r.max_score || 5);
            }
            (scoreMap[sec] as any).responses.push(r);
        }
    });

    const timelineEvents = logs.filter(l =>
        ['SECTION_START', 'ITEM_RENDERED', 'SESSION_START', 'SESSION_FINISHED', 'WINDOW_BLUR_EVT'].includes(l.event_type)
    );

    return (
        <div style={{ animation: 'fadeIn 0.4s ease-out' }}>
            <button onClick={() => router.push('/dashboard')} style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'none', border: 'none', color: THEME.teal, fontWeight: 600, cursor: 'pointer', marginBottom: 24, fontSize: 16 }}>
                <ArrowLeft size={20} /> Back to Roster
            </button>

            {/* HEADER */}
            <div style={{ background: THEME.white, padding: '32px', borderRadius: 16, boxShadow: '0 4px 15px rgba(0,0,0,0.03)', border: '1px solid #e2e8f0', marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h1 style={{ color: THEME.navy, fontSize: 32, margin: '0 0 8px 0', fontWeight: 800 }}>{session.student_name}</h1>
                    <div style={{ display: 'flex', gap: 16, color: '#64748b', fontSize: 14 }}>
                        <span>ID: {session.student_id}</span>
                        <span>•</span>
                        <span>Session: {session.id}</span>
                        <span>•</span>
                        <span>{new Date(session.start_time).toLocaleString()}</span>
                    </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: 13, textTransform: 'uppercase', color: '#94a3b8', fontWeight: 700, letterSpacing: 1, marginBottom: 4 }}>Total Score</div>
                    <div style={{ fontSize: 36, fontWeight: 900, color: THEME.navy }}>{session.total_score !== null ? session.total_score : '—'}</div>
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 350px', gap: 24 }}>
                {/* LEFT COL: Scores & Responses */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>

                    {/* SCORE BREAKDOWN */}
                    <div style={{ background: THEME.white, padding: '32px', borderRadius: 16, boxShadow: '0 4px 15px rgba(0,0,0,0.03)', border: '1px solid #e2e8f0' }}>
                        <h2 style={{ fontSize: 20, color: THEME.navy, fontWeight: 700, margin: '0 0 24px 0', borderBottom: '2px solid #f1f5f9', paddingBottom: 12 }}>Score Breakdown</h2>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
                            {['READING', 'LISTENING'].map(sec => {
                                const stats = scoreMap[sec as 'READING' | 'LISTENING'];
                                return (
                                    <div key={sec} style={{ background: '#f8fafc', padding: '20px', borderRadius: 12, border: '1px solid #e2e8f0' }}>
                                        <div style={{ color: '#64748b', fontSize: 12, fontWeight: 700, letterSpacing: 1, marginBottom: 8 }}>{sec} (DETERMINISTIC)</div>
                                        <div style={{ fontSize: 28, fontWeight: 800, color: THEME.teal }}>
                                            {stats.correct} <span style={{ fontSize: 16, color: '#94a3b8', fontWeight: 600 }}>/ {Math.max(stats.total, 1)}</span>
                                        </div>
                                        <div style={{ marginTop: 8, height: 6, background: '#e2e8f0', borderRadius: 4, overflow: 'hidden' }}>
                                            <div style={{ height: '100%', background: THEME.teal, width: `${(stats.correct / Math.max(stats.total, 1)) * 100}%` }} />
                                        </div>
                                    </div>
                                );
                            })}
                            {['SPEAKING', 'WRITING'].map(sec => {
                                const stats = scoreMap[sec as 'SPEAKING' | 'WRITING'];
                                return (
                                    <div key={sec} style={{ background: '#f8fafc', padding: '20px', borderRadius: 12, border: '1px solid #e2e8f0' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                                            <div style={{ color: '#64748b', fontSize: 12, fontWeight: 700, letterSpacing: 1 }}>{sec} (AI RUBRIC)</div>
                                            <BrainCircuit size={16} color={THEME.teal} />
                                        </div>
                                        <div style={{ fontSize: 28, fontWeight: 800, color: THEME.navy }}>
                                            {stats.crGiven} <span style={{ fontSize: 16, color: '#94a3b8', fontWeight: 600 }}>/ {Math.max(stats.maxScore, 1)} pts</span>
                                        </div>
                                        <div style={{ marginTop: 8, height: 6, background: '#e2e8f0', borderRadius: 4, overflow: 'hidden' }}>
                                            <div style={{ height: '100%', background: THEME.navy, width: `${(stats.crGiven / Math.max(stats.maxScore, 1)) * 100}%` }} />
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>

                    {/* PLAYBACK VAULT */}
                    <div style={{ background: THEME.white, padding: '32px', borderRadius: 16, boxShadow: '0 4px 15px rgba(0,0,0,0.03)', border: '1px solid #e2e8f0' }}>
                        <h2 style={{ fontSize: 20, color: THEME.navy, fontWeight: 700, margin: '0 0 24px 0', borderBottom: '2px solid #f1f5f9', paddingBottom: 12 }}>Playback Vault (Speaking)</h2>
                        {scoreMap['SPEAKING'].responses.length === 0 ? (
                            <div style={{ padding: 20, color: '#94a3b8', textAlign: 'center' }}>No speaking responses recorded.</div>
                        ) : (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                                {scoreMap['SPEAKING'].responses.map((r, i) => (
                                    <div key={r.id} style={{ padding: 20, background: '#f8fafc', borderRadius: 12, border: '1px solid #e2e8f0' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
                                            <div style={{ fontWeight: 600, color: THEME.navy }}>Prompt {i + 1}: {r.task_type}</div>
                                            <div style={{ background: THEME.tealLight, color: THEME.teal, padding: '4px 10px', borderRadius: 20, fontSize: 13, fontWeight: 700 }}>
                                                Score: {r.rubric_score}/{r.max_score || 5}
                                            </div>
                                        </div>
                                        {r.student_raw_response && r.student_raw_response.startsWith('/uploads') ? (
                                            <audio controls src={`${API_BASE_URL}${r.student_raw_response.replace('/uploads', '/api/audio')}`} style={{ width: '100%' }} />
                                        ) : (
                                            <div style={{ color: '#64748b', fontSize: 14, fontStyle: 'italic' }}>Audio unavailable (Raw path: {r.student_raw_response})</div>
                                        )}
                                        {r.ai_feedback && (
                                            <div style={{ marginTop: 16, fontSize: 14, color: THEME.text, background: 'white', padding: 16, borderRadius: 8, borderLeft: `4px solid ${THEME.navy}` }}>
                                                <strong style={{ display: 'block', marginBottom: 4, color: THEME.navy }}>AI Feedback:</strong>
                                                "{r.ai_feedback.feedback || JSON.stringify(r.ai_feedback)}"
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* WRITING RESPONSES */}
                    <div style={{ background: THEME.white, padding: '32px', borderRadius: 16, boxShadow: '0 4px 15px rgba(0,0,0,0.03)', border: '1px solid #e2e8f0' }}>
                        <h2 style={{ fontSize: 20, color: THEME.navy, fontWeight: 700, margin: '0 0 24px 0', borderBottom: '2px solid #f1f5f9', paddingBottom: 12 }}>Writing Vault</h2>
                        {scoreMap['WRITING'].responses.length === 0 ? (
                            <div style={{ padding: 20, color: '#94a3b8', textAlign: 'center' }}>No writing responses recorded.</div>
                        ) : (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                                {scoreMap['WRITING'].responses.map((r, i) => (
                                    <div key={r.id} style={{ padding: 20, background: '#f8fafc', borderRadius: 12, border: '1px solid #e2e8f0' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
                                            <div style={{ fontWeight: 600, color: THEME.navy }}>{r.task_type}</div>
                                            <div style={{ background: THEME.navy, color: 'white', padding: '4px 10px', borderRadius: 20, fontSize: 13, fontWeight: 700 }}>
                                                Score: {r.rubric_score}/{r.max_score || 5}
                                            </div>
                                        </div>
                                        <div style={{ fontSize: 15, lineHeight: 1.6, color: THEME.text, background: 'white', padding: '20px', borderRadius: 8, whiteSpace: 'pre-wrap', border: '1px solid #e2e8f0' }}>
                                            {r.student_raw_response}
                                        </div>
                                        {r.ai_feedback && (
                                            <div style={{ marginTop: 16, fontSize: 14, color: THEME.text }}>
                                                <strong style={{ display: 'block', marginBottom: 4, color: THEME.teal }}>Automated Feedback:</strong>
                                                {r.ai_feedback.feedback || JSON.stringify(r.ai_feedback)}
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* RIGHT COL: Timeline */}
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <div style={{ background: THEME.white, padding: '32px 24px', borderRadius: 16, boxShadow: '0 4px 15px rgba(0,0,0,0.03)', border: '1px solid #e2e8f0', flex: 1 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 24, paddingBottom: 12, borderBottom: '2px solid #f1f5f9' }}>
                            <Clock color={THEME.navy} size={20} />
                            <h2 style={{ fontSize: 18, color: THEME.navy, fontWeight: 700, margin: 0 }}>Behavioral Timeline</h2>
                        </div>

                        {timelineEvents.length === 0 ? (
                            <div style={{ color: '#94a3b8', fontSize: 14, textAlign: 'center', padding: 20 }}>No events logged for this session.</div>
                        ) : (
                            <div style={{ position: 'relative', paddingLeft: 12 }}>
                                {timelineEvents.map((evt, i) => {
                                    const time = new Date(evt.event_timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
                                    const isSuspicious = evt.event_type === 'WINDOW_BLUR_EVT';

                                    let icon = <CheckCircle size={14} color="#94a3b8" />;
                                    if (isSuspicious) icon = <AlertTriangle size={14} color={THEME.error} />;
                                    else if (evt.event_type.includes('SECTION')) icon = <FileText size={14} color={THEME.teal} />;

                                    return (
                                        <div key={evt.id} style={{ display: 'flex', gap: 16, marginBottom: 24, position: 'relative' }}>
                                            {/* Line */}
                                            {i !== timelineEvents.length - 1 && (
                                                <div style={{ position: 'absolute', left: 6, top: 20, bottom: -24, width: 2, background: '#e2e8f0' }} />
                                            )}
                                            {/* Point */}
                                            <div style={{ width: 14, height: 14, position: 'relative', zIndex: 2, background: 'white', marginTop: 4 }}>
                                                {icon}
                                            </div>
                                            {/* Content */}
                                            <div style={{ flex: 1, paddingTop: 2 }}>
                                                <div style={{ fontSize: 12, color: '#94a3b8', fontWeight: 600, marginBottom: 2 }}>{time}</div>
                                                <div style={{ fontSize: 14, fontWeight: 700, color: isSuspicious ? THEME.error : THEME.navy }}>
                                                    {evt.event_type.replace(/_/g, ' ')}
                                                </div>
                                                {evt.event_data && (
                                                    <div style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>
                                                        {evt.event_data.section && `Section: ${evt.event_data.section}`}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            <style>{`
                @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
            `}</style>
        </div>
    );
}
