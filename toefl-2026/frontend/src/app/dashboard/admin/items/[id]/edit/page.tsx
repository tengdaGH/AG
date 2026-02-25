'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/Card';
import { Button } from '@/components/Button';
import { Input } from '@/components/Input';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { API_BASE_URL } from '@/lib/api-config';

interface Question {
    question_num: number;
    text: string;
    options: string[];
    correct_answer: number;
}

interface PromptContent {
    type: string;
    title: string;
    text: string;
    questions: Question[];
}

interface ItemData {
    id: string;
    section: string;
    target_level: string;
    irt_difficulty: number;
    irt_discrimination: number;
    prompt_content: string;
    lifecycle_status: string;
    is_active: boolean;
}

interface ReviewLog {
    id: string;
    stage_name: string;
    reviewer: string;
    action: string;
    notes: string;
    timestamp: string;
}

interface VersionLog {
    id: string;
    version_number: number;
    prompt_content: string;
    changed_by: string;
    timestamp: string;
}

export default function ItemEditor() {
    const params = useParams();
    const router = useRouter();
    const searchParams = useSearchParams();
    const itemId = params.id as string;

    const [loading, setLoading] = useState(true);
    const [mode, setMode] = useState<'edit' | 'preview' | 'history'>(searchParams.get('mode') === 'history' ? 'history' : 'edit');
    const [historyData, setHistoryData] = useState<{ reviews: ReviewLog[], versions: VersionLog[] }>({ reviews: [], versions: [] });


    // Item metadata
    const [sectionType, setSectionType] = useState('READING');
    const [targetCEFR, setTargetCEFR] = useState('B2');
    const [difficulty, setDifficulty] = useState('0.5');
    const [discrimination, setDiscrimination] = useState('1.0');
    const [lifecycleStatus, setLifecycleStatus] = useState('DRAFT');
    const [isActive, setIsActive] = useState(true);

    // Parsed content
    const [itemType, setItemType] = useState('');
    const [title, setTitle] = useState('');
    const [passageText, setPassageText] = useState('');
    const [questions, setQuestions] = useState<Question[]>([]);

    useEffect(() => {
        const fetchItem = async () => {
            try {
                const res = await fetch(`${API_BASE_URL}/api/items/${itemId}`, {
                    headers: {
                        'Bypass-Tunnel-Reminders': 'true'
                    }
                });
                if (res.ok) {
                    const data: ItemData = await res.json();
                    setSectionType(data.section);
                    setTargetCEFR(data.target_level);
                    setDifficulty(String(data.irt_difficulty));
                    setDiscrimination(String(data.irt_discrimination));
                    setLifecycleStatus(data.lifecycle_status || 'DRAFT');
                    setIsActive(data.is_active);

                    const parsed: PromptContent = typeof data.prompt_content === 'string'
                        ? JSON.parse(data.prompt_content)
                        : data.prompt_content;
                    setItemType(parsed.type || '');
                    setTitle(parsed.title || '');
                    setPassageText(parsed.text || '');
                    setQuestions(parsed.questions || []);
                }
            } catch (error) {
                console.error('Failed to load item:', error);
            } finally {
                setLoading(false);
            }
        };

        const fetchHistory = async () => {
            try {
                const res = await fetch(`${API_BASE_URL}/api/items/${itemId}/history`, {
                    headers: { 'Bypass-Tunnel-Reminders': 'true' }
                });
                if (res.ok) {
                    const data = await res.json();
                    setHistoryData(data);
                }
            } catch (error) {
                console.error('Failed to load history:', error);
            }
        };

        fetchItem();
        fetchHistory();
    }, [itemId]);

    const handleSave = async () => {
        try {
            const updatedContent: PromptContent = {
                type: itemType,
                title,
                text: passageText,
                questions,
            };

            const response = await fetch(`${API_BASE_URL}/api/items/${itemId}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Bypass-Tunnel-Reminders': 'true'
                },
                body: JSON.stringify({
                    section: sectionType,
                    target_level: targetCEFR,
                    irt_difficulty: parseFloat(difficulty),
                    irt_discrimination: parseFloat(discrimination),
                    lifecycle_status: lifecycleStatus,
                    is_active: lifecycleStatus === 'ACTIVE' || lifecycleStatus === 'FIELD_TEST',
                    prompt_content: JSON.stringify(updatedContent)
                })
            });

            if (response.ok) {
                alert('Item saved successfully!');
                router.push('/dashboard/admin/items');
            } else {
                const err = await response.json();
                alert(`Failed to save: ${err.detail || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Save error:', error);
            alert('An error occurred while saving.');
        }
    };

    // ─── TYPE-SPECIFIC RENDERERS ───

    const renderAcademicPassageEditor = () => (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div>
                <label style={labelStyle}>Passage Title</label>
                <Input value={title} onChange={(e) => setTitle(e.target.value)} fullWidth />
            </div>
            <div>
                <label style={labelStyle}>Academic Passage (~200 words)</label>
                <textarea value={passageText} onChange={(e) => setPassageText(e.target.value)}
                    style={{ ...textareaStyle, height: '220px' }} />
                <div style={helperStyle}>{passageText.split(/\s+/).filter(Boolean).length} / 200 words</div>
            </div>
            {questions.map((q, i) => (
                <div key={i} style={questionBlockStyle}>
                    <label style={labelStyle}>Question {q.question_num}</label>
                    <Input value={q.text} onChange={(e) => { const nq = [...questions]; nq[i] = { ...nq[i], text: e.target.value }; setQuestions(nq); }} fullWidth />
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', marginTop: '0.5rem' }}>
                        {q.options.map((opt, oi) => (
                            <div key={oi} style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                                <input type="radio" name={`q${i}`} checked={q.correct_answer === oi} onChange={() => { const nq = [...questions]; nq[i] = { ...nq[i], correct_answer: oi }; setQuestions(nq); }} />
                                <Input value={opt} onChange={(e) => { const nq = [...questions]; const nopts = [...nq[i].options]; nopts[oi] = e.target.value; nq[i] = { ...nq[i], options: nopts }; setQuestions(nq); }} fullWidth style={{ marginBottom: 0 }} />
                            </div>
                        ))}
                    </div>
                </div>
            ))}
        </div>
    );

    const renderDailyLifeEditor = () => (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div>
                <label style={labelStyle}>Notice / Email Title</label>
                <Input value={title} onChange={(e) => setTitle(e.target.value)} fullWidth />
            </div>
            <div>
                <label style={labelStyle}>Daily Life Text (15–150 words)</label>
                <textarea value={passageText} onChange={(e) => setPassageText(e.target.value)}
                    style={{ ...textareaStyle, height: '150px' }} />
                <div style={helperStyle}>{passageText.split(/\s+/).filter(Boolean).length} / 150 words max</div>
            </div>
            {questions.map((q, i) => (
                <div key={i} style={questionBlockStyle}>
                    <label style={labelStyle}>Question {q.question_num}</label>
                    <Input value={q.text} onChange={(e) => { const nq = [...questions]; nq[i] = { ...nq[i], text: e.target.value }; setQuestions(nq); }} fullWidth />
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', marginTop: '0.5rem' }}>
                        {q.options.map((opt, oi) => (
                            <div key={oi} style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                                <input type="radio" name={`q${i}`} checked={q.correct_answer === oi} onChange={() => { const nq = [...questions]; nq[i] = { ...nq[i], correct_answer: oi }; setQuestions(nq); }} />
                                <Input value={opt} onChange={(e) => { const nq = [...questions]; const nopts = [...nq[i].options]; nopts[oi] = e.target.value; nq[i] = { ...nq[i], options: nopts }; setQuestions(nq); }} fullWidth style={{ marginBottom: 0 }} />
                            </div>
                        ))}
                    </div>
                </div>
            ))}
        </div>
    );

    const renderCompleteTheWordsEditor = () => (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div>
                <label style={labelStyle}>C-Test Title</label>
                <Input value={title} onChange={(e) => setTitle(e.target.value)} fullWidth />
            </div>
            <div>
                <label style={labelStyle}>Paragraph with Blanks (use underscores for missing letters)</label>
                <textarea value={passageText} onChange={(e) => setPassageText(e.target.value)}
                    style={{ ...textareaStyle, height: '180px' }} />
                <div style={helperStyle}>Use underscores like temp___atures. 10 truncated words per C-test spec.</div>
            </div>
            {questions.map((q, i) => (
                <div key={i} style={questionBlockStyle}>
                    <label style={labelStyle}>Answer Options</label>
                    <Input value={q.text} onChange={(e) => { const nq = [...questions]; nq[i] = { ...nq[i], text: e.target.value }; setQuestions(nq); }} fullWidth />
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', marginTop: '0.5rem' }}>
                        {q.options.map((opt, oi) => (
                            <div key={oi} style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                                <input type="radio" name={`q${i}`} checked={q.correct_answer === oi} onChange={() => { const nq = [...questions]; nq[i] = { ...nq[i], correct_answer: oi }; setQuestions(nq); }} />
                                <Input value={opt} onChange={(e) => { const nq = [...questions]; const nopts = [...nq[i].options]; nopts[oi] = e.target.value; nq[i] = { ...nq[i], options: nopts }; setQuestions(nq); }} fullWidth style={{ marginBottom: 0 }} />
                            </div>
                        ))}
                    </div>
                </div>
            ))}
        </div>
    );

    const renderEditorByType = () => {
        if (itemType.includes('Academic')) return renderAcademicPassageEditor();
        if (itemType.includes('Daily Life')) return renderDailyLifeEditor();
        if (itemType.includes('Complete')) return renderCompleteTheWordsEditor();
        // Fallback for unknown types
        return renderAcademicPassageEditor();
    };

    // ─── PREVIEW RENDERERS ───

    const renderAcademicPassagePreview = () => (
        <div style={{ padding: '2rem', fontFamily: 'var(--font-body)', lineHeight: 1.8 }}>
            <div style={{ backgroundColor: '#1e293b', color: 'white', padding: '0.75rem 1.25rem', borderRadius: '8px 8px 0 0', fontSize: '0.8rem', fontFamily: 'var(--font-sans)', fontWeight: 600 }}>
                TOEFL 2026 — Reading Section: Read an Academic Passage
            </div>
            <div style={{ border: '1px solid #cbd5e1', borderTop: 'none', borderRadius: '0 0 8px 8px', padding: '2rem', backgroundColor: 'white' }}>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '1rem', fontFamily: 'var(--font-sans)' }}>{title}</h2>
                <p style={{ fontSize: '1rem', color: '#334155', whiteSpace: 'pre-wrap' }}>{passageText}</p>
                <hr style={{ margin: '1.5rem 0', borderColor: '#e2e8f0' }} />
                {questions.map((q, i) => (
                    <div key={i} style={{ marginBottom: '1.5rem' }}>
                        <p style={{ fontWeight: 600, marginBottom: '0.5rem', fontFamily: 'var(--font-sans)', fontSize: '0.95rem' }}>
                            {q.question_num}. {q.text}
                        </p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', paddingLeft: '1rem' }}>
                            {q.options.map((opt, oi) => (
                                <label key={oi} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', padding: '0.4rem 0.6rem', borderRadius: '6px', fontSize: '0.9rem', fontFamily: 'var(--font-sans)' }}>
                                    <input type="radio" name={`preview-q${i}`} disabled /> {String.fromCharCode(65 + oi)}. {opt}
                                </label>
                            ))}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );

    const renderDailyLifePreview = () => (
        <div style={{ padding: '2rem' }}>
            <div style={{ backgroundColor: '#0369a1', color: 'white', padding: '0.75rem 1.25rem', borderRadius: '8px 8px 0 0', fontSize: '0.8rem', fontFamily: 'var(--font-sans)', fontWeight: 600 }}>
                TOEFL 2026 — Reading Section: Read in Daily Life
            </div>
            <div style={{ border: '2px solid #bae6fd', borderTop: 'none', borderRadius: '0 0 8px 8px', padding: '1.5rem', backgroundColor: '#f0f9ff' }}>
                <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '1.25rem', border: '1px solid #e0f2fe', marginBottom: '1.5rem' }}>
                    <h3 style={{ fontWeight: 700, fontSize: '1.1rem', marginBottom: '0.75rem' }}>{title}</h3>
                    <p style={{ fontSize: '0.95rem', lineHeight: 1.7, color: '#334155', whiteSpace: 'pre-wrap' }}>{passageText}</p>
                </div>
                {questions.map((q, i) => (
                    <div key={i} style={{ marginBottom: '1.25rem' }}>
                        <p style={{ fontWeight: 600, marginBottom: '0.5rem', fontSize: '0.95rem' }}>{q.question_num}. {q.text}</p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', paddingLeft: '1rem' }}>
                            {q.options.map((opt, oi) => (
                                <label key={oi} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', padding: '0.35rem 0.5rem', fontSize: '0.9rem' }}>
                                    <input type="radio" name={`preview-q${i}`} disabled /> {String.fromCharCode(65 + oi)}. {opt}
                                </label>
                            ))}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );

    const renderCompleteTheWordsPreview = () => (
        <div style={{ padding: '2rem' }}>
            <div style={{ backgroundColor: '#7c3aed', color: 'white', padding: '0.75rem 1.25rem', borderRadius: '8px 8px 0 0', fontSize: '0.8rem', fontFamily: 'var(--font-sans)', fontWeight: 600 }}>
                TOEFL 2026 — Reading Section: Complete the Words (C-test)
            </div>
            <div style={{ border: '2px solid #ddd6fe', borderTop: 'none', borderRadius: '0 0 8px 8px', padding: '2rem', backgroundColor: '#faf5ff' }}>
                <p style={{ fontSize: '1rem', lineHeight: 2, color: '#334155', whiteSpace: 'pre-wrap', fontFamily: 'var(--font-body)' }}>
                    {passageText.split(/(_+)/).map((part, index) =>
                        part.match(/_+/) ? (
                            <span key={index} style={{
                                display: 'inline-block',
                                borderBottom: '2px solid #7c3aed',
                                minWidth: `${part.length * 10}px`,
                                padding: '0 4px',
                                margin: '0 2px',
                                color: '#7c3aed',
                                fontWeight: 600,
                            }}>{part}</span>
                        ) : <span key={index}>{part}</span>
                    )}
                </p>
                <hr style={{ margin: '1.5rem 0', borderColor: '#ddd6fe' }} />
                <p style={{ fontWeight: 600, marginBottom: '1rem', fontSize: '0.95rem', color: '#475569' }}>Fill in the missing letters:</p>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.75rem' }}>
                    {questions.map((q, i) => (
                        <div key={i} style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.75rem',
                            padding: '0.5rem 0.75rem',
                            backgroundColor: 'white',
                            borderRadius: '6px',
                            border: '1px solid #e2e8f0',
                        }}>
                            <span style={{ fontWeight: 700, color: '#7c3aed', fontSize: '0.85rem', minWidth: '1.5rem' }}>{q.question_num || i + 1}.</span>
                            <span style={{ fontFamily: 'monospace', color: '#64748b', fontSize: '0.9rem' }}>{q.text}</span>
                            <span style={{ color: '#94a3b8', fontSize: '0.85rem' }}>→</span>
                            <span style={{ fontWeight: 600, color: '#059669', fontSize: '0.9rem' }}>
                                {q.correct_answer || q.options?.[q.correct_answer as unknown as number] || '—'}
                            </span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );

    const renderPreviewByType = () => {
        if (itemType.includes('Academic')) return renderAcademicPassagePreview();
        if (itemType.includes('Daily Life')) return renderDailyLifePreview();
        if (itemType.includes('Complete')) return renderCompleteTheWordsPreview();
        return renderAcademicPassagePreview();
    };

    const renderHistoryView = () => (
        <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            <div>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 600, color: '#1e293b', marginBottom: '1rem', borderBottom: '2px solid #e2e8f0', paddingBottom: '0.5rem' }}>
                    QA Review Audit Trail
                </h3>
                {historyData.reviews.length === 0 ? (
                    <p style={{ color: '#64748b', fontSize: '0.9rem' }}>No automated or human reviews logged yet.</p>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                        {historyData.reviews.map((r) => (
                            <div key={r.id} style={{ display: 'flex', gap: '1rem', padding: '1rem', borderRadius: '8px', backgroundColor: r.action === 'PASS' ? '#f0fdf4' : '#fef2f2', border: `1px solid ${r.action === 'PASS' ? '#bbf7d0' : '#fecaca'}` }}>
                                <div style={{ minWidth: '120px' }}>
                                    <div style={{ fontWeight: 700, fontSize: '0.85rem', color: r.action === 'PASS' ? '#16a34a' : '#dc2626' }}>{r.action}</div>
                                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{new Date(r.timestamp).toLocaleString()}</div>
                                </div>
                                <div style={{ flex: 1 }}>
                                    <div style={{ fontWeight: 600, fontSize: '0.9rem', color: '#334155' }}>[{r.stage_name}] Reviewer: {r.reviewer}</div>
                                    {r.notes && <div style={{ marginTop: '0.25rem', fontSize: '0.85rem', color: '#475569', backgroundColor: 'rgba(255,255,255,0.6)', padding: '0.5rem', borderRadius: '4px' }}>{r.notes}</div>}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            <div>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 600, color: '#1e293b', marginBottom: '1rem', borderBottom: '2px solid #e2e8f0', paddingBottom: '0.5rem' }}>
                    Psychometric Version History
                </h3>
                {historyData.versions.length === 0 ? (
                    <p style={{ color: '#64748b', fontSize: '0.9rem' }}>No older versions exist. This is Version 1.</p>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                        {historyData.versions.map((v) => (
                            <div key={v.id} style={{ padding: '1rem', borderRadius: '8px', backgroundColor: '#f8fafc', border: '1px solid #cbd5e1' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                                    <span style={{ fontWeight: 600, fontSize: '0.95rem', color: '#334155' }}>Version {v.version_number}</span>
                                    <span style={{ fontSize: '0.75rem', color: '#64748b' }}>{new Date(v.timestamp).toLocaleString()} • {v.changed_by}</span>
                                </div>
                                <details style={{ cursor: 'pointer', fontSize: '0.85rem', color: '#475569' }}>
                                    <summary style={{ outline: 'none', fontWeight: 500 }}>View Raw Payload Snapshot</summary>
                                    <pre style={{ marginTop: '0.5rem', backgroundColor: '#f1f5f9', padding: '1rem', borderRadius: '6px', overflowX: 'auto', whiteSpace: 'pre-wrap', maxHeight: '400px', overflowY: 'auto' }}>
                                        {v.prompt_content}
                                    </pre>
                                </details>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );


    // ─── STYLES ───
    const labelStyle: React.CSSProperties = { fontSize: '0.875rem', fontWeight: 600, color: 'var(--foreground)', display: 'block', marginBottom: '0.5rem' };
    const helperStyle: React.CSSProperties = { fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' };
    const textareaStyle: React.CSSProperties = { width: '100%', padding: '1rem', borderRadius: '6px', border: '1px solid var(--border-color)', resize: 'vertical', fontFamily: 'var(--font-mono)', fontSize: '0.875rem', lineHeight: 1.6, backgroundColor: 'var(--card-bg)' };
    const questionBlockStyle: React.CSSProperties = { padding: '1rem', borderRadius: '8px', backgroundColor: '#f8fafc', border: '1px solid var(--border-color)' };

    const typeLabel: Record<string, { label: string; color: string }> = {
        'Read an Academic Passage': { label: '📖 Academic Passage', color: '#1e293b' },
        'Academic Passage': { label: '📖 Academic Passage', color: '#1e293b' },
        'Read in Daily Life': { label: '📬 Read in Daily Life', color: '#0369a1' },
        'Complete the Words': { label: '✏️ Complete the Words (C-test)', color: '#7c3aed' },
    };

    const currentTypeInfo = typeLabel[itemType] || { label: itemType, color: '#475569' };

    if (loading) {
        return (
            <div className="app-layout" style={{ backgroundColor: 'var(--background)', minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <p>Loading item...</p>
            </div>
        );
    }

    return (
        <div className="app-layout" style={{ backgroundColor: 'var(--background)' }}>
            <header style={{ padding: '1rem 2rem', borderBottom: '1px solid var(--border-color)', backgroundColor: 'var(--card-bg)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{ width: '32px', height: '32px', backgroundColor: currentTypeInfo.color, borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 'bold', fontSize: '0.8rem' }}>✎</div>
                    <div>
                        <span style={{ fontWeight: 600, fontSize: '1.25rem' }}>Edit Item</span>
                        <span style={{ marginLeft: '0.75rem', fontSize: '0.85rem', color: currentTypeInfo.color, fontWeight: 600, backgroundColor: `${currentTypeInfo.color}15`, padding: '0.2rem 0.6rem', borderRadius: '999px' }}>
                            {currentTypeInfo.label}
                        </span>
                    </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <Button variant="ghost" size="sm" onClick={() => router.push('/dashboard/admin/items')}>← Back to Item Bank</Button>
                    <Button size="sm" onClick={handleSave}>💾 Save Changes</Button>
                </div>
            </header>

            <main className="container" style={{ paddingTop: '2rem', paddingBottom: '2rem', display: 'flex', gap: '2rem', maxWidth: '1400px' }}>

                {/* Left Column: Metadata */}
                <div style={{ width: '320px', display: 'flex', flexDirection: 'column', gap: '1.5rem', flexShrink: 0 }}>
                    <Card>
                        <CardHeader><CardTitle>Item Metadata</CardTitle></CardHeader>
                        <CardContent style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                            <div>
                                <label style={labelStyle}>Item Type</label>
                                <div style={{ padding: '0.625rem 0.75rem', borderRadius: '6px', backgroundColor: `${currentTypeInfo.color}10`, border: `1px solid ${currentTypeInfo.color}30`, color: currentTypeInfo.color, fontWeight: 600, fontSize: '0.875rem' }}>
                                    {currentTypeInfo.label}
                                </div>
                            </div>
                            <div>
                                <label style={labelStyle}>Section Type</label>
                                <select value={sectionType} onChange={(e) => setSectionType(e.target.value)}
                                    style={{ width: '100%', height: '2.5rem', borderRadius: '6px', border: '1px solid var(--border-color)', padding: '0 0.75rem', backgroundColor: 'var(--card-bg)' }}>
                                    <option value="READING">Reading (Multi-Stage Adaptive)</option>
                                    <option value="LISTENING">Listening (Multi-Stage Adaptive)</option>
                                    <option value="SPEAKING">Speaking (Virtual Interview)</option>
                                    <option value="WRITING">Writing (Write an Email)</option>
                                </select>
                            </div>
                            <div>
                                <label style={labelStyle}>Target CEFR Level</label>
                                <select value={targetCEFR} onChange={(e) => setTargetCEFR(e.target.value)}
                                    style={{ width: '100%', height: '2.5rem', borderRadius: '6px', border: '1px solid var(--border-color)', padding: '0 0.75rem', backgroundColor: 'var(--card-bg)' }}>
                                    <option value="A2">A2 (Entry)</option>
                                    <option value="B1">B1 (Intermediate)</option>
                                    <option value="B2">B2 (Upper Intermediate)</option>
                                    <option value="C1">C1 (Advanced)</option>
                                    <option value="C2">C2 (Mastery)</option>
                                </select>
                            </div>
                            <div style={{ paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
                                <h4 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '1rem', color: 'var(--text-muted)' }}>IRT PARAMETERS (3PL MODEL)</h4>
                                <Input label="Difficulty (b-parameter)" type="number" step="0.1" min="-3.0" max="3.0"
                                    value={difficulty} onChange={(e) => setDifficulty(e.target.value)} helperText="Range: -3.0 (Easy) to +3.0 (Hard)" />
                                <Input label="Discrimination (a-parameter)" type="number" step="0.1" min="0.5" max="2.5"
                                    value={discrimination} onChange={(e) => setDiscrimination(e.target.value)} helperText="Range: 0.5 (Low) to 2.5 (High)" />
                            </div>
                            <div style={{ paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
                                <label style={labelStyle}>Lifecycle Status</label>
                                <select value={lifecycleStatus} onChange={(e) => setLifecycleStatus(e.target.value)}
                                    style={{ width: '100%', height: '2.5rem', borderRadius: '6px', border: '2px solid #3b82f6', padding: '0 0.75rem', backgroundColor: '#eff6ff', fontWeight: 600 }}>
                                    <option value="DRAFT">Draft (Authoring)</option>
                                    <option value="REVIEW">Review (QA/Editing)</option>
                                    <option value="FIELD_TEST">Field Test (Unscored)</option>
                                    <option value="ACTIVE">Active (Live)</option>
                                    <option value="SUSPENDED">Suspended (Issues)</option>
                                    <option value="EXPOSED">Exposed (Leaked)</option>
                                    <option value="ARCHIVED">Archived (Retired)</option>
                                </select>
                                <div style={{ ...helperStyle, color: '#3b82f6' }}>Professional lifecycle tracking enabled</div>
                            </div>
                            <div style={{ paddingTop: '1rem', borderTop: '1px solid var(--border-color)', opacity: 0.6 }}>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem', fontWeight: 500 }}>
                                    <input type="checkbox" checked={lifecycleStatus === 'ACTIVE' || lifecycleStatus === 'FIELD_TEST'} readOnly />
                                    Active for Engine (Inherited)
                                </label>
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Right Column: Content Editor / Preview */}
                <div style={{ flex: 1 }}>
                    <Card style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                        <CardHeader style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '1.5rem', backgroundColor: '#f8fafc' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <CardTitle>{mode === 'edit' ? 'Content Editor' : 'Student Preview'}</CardTitle>
                                <div style={{ display: 'flex', gap: '0.25rem', backgroundColor: '#e2e8f0', borderRadius: '8px', padding: '0.2rem' }}>
                                    <button onClick={() => setMode('edit')} style={{
                                        padding: '0.4rem 1rem', borderRadius: '6px', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer', border: 'none',
                                        backgroundColor: mode === 'edit' ? 'white' : 'transparent',
                                        color: mode === 'edit' ? '#1e293b' : '#64748b',
                                        boxShadow: mode === 'edit' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                                    }}>✏️ Edit</button>
                                    <button onClick={() => setMode('preview')} style={{
                                        padding: '0.4rem 1rem', borderRadius: '6px', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer', border: 'none',
                                        backgroundColor: mode === 'preview' ? 'white' : 'transparent',
                                        color: mode === 'preview' ? '#1e293b' : '#64748b',
                                        boxShadow: mode === 'preview' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                                    }}>👁 Preview</button>
                                    <button onClick={() => setMode('history')} style={{
                                        padding: '0.4rem 1rem', borderRadius: '6px', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer', border: 'none',
                                        backgroundColor: mode === 'history' ? 'white' : 'transparent',
                                        color: mode === 'history' ? '#1e293b' : '#64748b',
                                        boxShadow: mode === 'history' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                                    }}>📜 History</button>
                                </div>
                            </div>
                        </CardHeader>
                        <CardContent style={{ flex: 1, padding: mode === 'preview' || mode === 'history' ? 0 : '1.5rem', overflow: 'auto' }}>
                            {mode === 'edit' && renderEditorByType()}
                            {mode === 'preview' && renderPreviewByType()}
                            {mode === 'history' && renderHistoryView()}
                        </CardContent>
                    </Card>
                </div>

            </main>
        </div>
    );
}
