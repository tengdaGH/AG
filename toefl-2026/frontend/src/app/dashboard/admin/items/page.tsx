'use client';

import React, { useState, useEffect, useMemo, memo } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/Card';
import { Button } from '@/components/Button';
import { Input } from '@/components/Input';
import { useLanguage } from '@/lib/i18n/LanguageContext';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';
import { useRouter } from 'next/navigation';

import { normaliseContent, TASK_TYPE_LABELS, getItemAge, type ParsedContent, type Question } from '@/lib/content-utils';
import { API_BASE_URL } from '@/lib/api-config';


// ─── PREVIEW MODAL ───
function PreviewModal({ item, parsedContent: rawContent, onClose }: { item: any; parsedContent: any; onClose: () => void }) {
    const parsedContent = normaliseContent(rawContent, item);
    const [history, setHistory] = useState<any>(null);
    const [showHistory, setShowHistory] = useState(false);
    const [loadingHistory, setLoadingHistory] = useState(false);

    const fetchHistory = async () => {
        if (history) return;
        setLoadingHistory(true);
        try {
            const res = await fetch(`${API_BASE_URL}/api/items/${item.id}/history`, {
                headers: {
                    'Bypass-Tunnel-Reminder': 'true'
                }
            });
            const data = await res.json();
            setHistory(data);
        } catch (err) {
            console.error("Failed to fetch history:", err);
        } finally {
            setLoadingHistory(false);
        }
    };

    useEffect(() => {
        if (showHistory) {
            fetchHistory();
        }
    }, [showHistory]);

    const typeColors: Record<string, { bg: string; header: string; border: string }> = {
        'Read an Academic Passage': { bg: 'var(--anthropic-cream)', header: 'var(--anthropic-dark)', border: 'var(--anthropic-light-gray)' },
        'Academic Passage': { bg: 'var(--anthropic-cream)', header: 'var(--anthropic-dark)', border: 'var(--anthropic-light-gray)' },
        'Read in Daily Life': { bg: 'var(--anthropic-cream)', header: 'var(--anthropic-blue)', border: 'var(--anthropic-light-gray)' },
        'Complete the Words': { bg: 'var(--anthropic-cream)', header: 'var(--anthropic-terracotta)', border: 'var(--anthropic-light-gray)' },
        'Listen and Choose a Response': { bg: 'var(--anthropic-cream)', header: 'var(--anthropic-sage)', border: 'var(--anthropic-light-gray)' },
        'Listen to an Academic Talk': { bg: 'var(--anthropic-cream)', header: 'var(--anthropic-sage)', border: 'var(--anthropic-light-gray)' },
        'Listen to an Announcement': { bg: 'var(--anthropic-cream)', header: 'var(--anthropic-sage)', border: 'var(--anthropic-light-gray)' },
        'Listen to a Conversation': { bg: 'var(--anthropic-cream)', header: 'var(--anthropic-sage)', border: 'var(--anthropic-light-gray)' },
    };
    const colors = typeColors[parsedContent.type] || typeColors['Read an Academic Passage'];

    const isComplete = parsedContent.type.includes('Complete');
    const isBuildSentence = Array.isArray(rawContent.fragments);
    const hasQuestions = parsedContent.questions.length > 0;
    const sectionLabel =
        item.section === 'WRITING' ? 'Writing' :
            item.section === 'SPEAKING' ? 'Speaking' :
                item.section === 'LISTENING' ? 'Listening' : 'Reading';

    // Default title fallback logic
    let fallbackTitle = parsedContent.title;
    if (!fallbackTitle || fallbackTitle === 'Untitled Item' || fallbackTitle === item.id) {
        if (parsedContent.text) {
            const words = parsedContent.text.split(' ').slice(0, 8).join(' ');
            fallbackTitle = words + (parsedContent.text.length > words.length ? '...' : '');
        } else if (parsedContent.script) {
            const words = parsedContent.script.split(' ').slice(0, 8).join(' ');
            fallbackTitle = words + (parsedContent.script.length > words.length ? '...' : '');
        } else {
            fallbackTitle = item.task_type || parsedContent.type || 'Untitled Item';
        }
    }

    // For Build a Sentence, show a short preview of the sentence as title
    const displayTitle = isBuildSentence
        ? (() => {
            const frags = rawContent.fragments || [];
            const ep = rawContent.endPunctuation || '.';
            if (frags.length === 0) return 'Build a Sentence';
            const cap = [...frags];
            cap[0] = cap[0].charAt(0).toUpperCase() + cap[0].slice(1);
            return cap.join(' ') + ep;
        })()
        : fallbackTitle;

    return (
        <div onClick={onClose} style={{
            position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.8)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999,
            backdropFilter: 'blur(4px)', animation: 'fadeIn 0.15s ease-out',
        }}>
            <div onClick={(e) => e.stopPropagation()} style={{
                backgroundColor: 'var(--anthropic-cream)', borderRadius: '12px', width: '1000px', maxHeight: '90vh',
                overflow: 'auto', boxShadow: '0 25px 50px rgba(0,0,0,0.1)',
                display: 'flex', flexDirection: 'column', border: '1px solid var(--anthropic-light-gray)'
            }}>
                {/* Modal Header */}
                <div style={{
                    padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--anthropic-light-gray)',
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    position: 'sticky', top: 0, backgroundColor: 'var(--anthropic-cream)', zIndex: 1, borderRadius: '12px 12px 0 0',
                }}>
                    <div>
                        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.25rem', color: 'var(--anthropic-dark)' }}>{displayTitle}</h2>
                        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', fontSize: '0.75rem', fontFamily: 'var(--font-body)', color: 'var(--text-muted)' }}>
                            <span style={{ border: `1px solid ${colors.header}`, color: colors.header, padding: '0.15rem 0.5rem', borderRadius: '4px', fontWeight: 500 }}>
                                {parsedContent.type}
                            </span>
                            <span>{item.target_level} • b={item.irt_difficulty}</span>
                            <span style={{ color: 'var(--anthropic-blue)', fontWeight: 600 }}>v{item.version || 1}</span>
                            <span>• {item.generated_by_model || 'Unknown'}</span>
                            <span>• Age: {getItemAge(item.created_at)}</span>
                        </div>
                    </div>
                    <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                        <button onClick={() => setShowHistory(!showHistory)} style={{
                            padding: '0.4rem 1rem', borderRadius: '6px', fontSize: '0.85rem', fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-body)',
                            border: showHistory ? '1px solid var(--anthropic-blue)' : '1px solid var(--anthropic-light-gray)',
                            backgroundColor: showHistory ? 'rgba(106, 155, 204, 0.1)' : 'transparent',
                            color: showHistory ? 'var(--anthropic-blue)' : 'var(--anthropic-dark)',
                            display: 'flex', alignItems: 'center', gap: '0.35rem',
                            transition: 'all 0.2s'
                        }}>
                            <span>📜</span> {showHistory ? 'Hide History' : 'History'}
                        </button>
                        <button onClick={onClose} style={{
                            width: '32px', height: '32px', borderRadius: '8px', border: 'none',
                            backgroundColor: 'transparent', cursor: 'pointer', fontSize: '1.1rem', color: 'var(--anthropic-mid-gray)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center', transition: 'color 0.2s'
                        }}>✕</button>
                    </div>
                </div>

                {/* Simulated Test View */}
                <div style={{ padding: '2rem 1.5rem', fontFamily: 'var(--font-body)' }}>
                    {/* ─── AUDIO PLAYER ─── */}
                    {parsedContent.audioUrl && (
                        <div style={{
                            marginBottom: '1.5rem', padding: '1rem', backgroundColor: 'var(--card-bg)',
                            border: '1px solid var(--anthropic-light-gray)', borderRadius: '8px',
                            display: 'flex', flexDirection: 'column', gap: '0.75rem'
                        }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--anthropic-blue)', fontWeight: 600, fontSize: '0.85rem' }}>
                                <span>🔊</span> Listening Material
                            </div>
                            <audio
                                controls
                                src={parsedContent.audioUrl.startsWith('http') ? parsedContent.audioUrl : `/${parsedContent.audioUrl}`}
                                style={{ width: '100%', height: '36px' }}
                            />
                        </div>
                    )}
                    {/* ─── BUILD A SENTENCE PREVIEW ─── */}
                    {isBuildSentence ? (() => {
                        const fragments: string[] = rawContent.fragments || [];
                        const endPunct: string = rawContent.endPunctuation || '.';
                        const context: string = rawContent.context || '';
                        // Correct sentence: capitalize first word, add end punctuation
                        const correctFragments = [...fragments];
                        if (correctFragments.length > 0) {
                            correctFragments[0] = correctFragments[0].charAt(0).toUpperCase() + correctFragments[0].slice(1);
                            correctFragments[correctFragments.length - 1] += endPunct;
                        }
                        // Shuffled word bank (deterministic from item id for consistency)
                        const shuffled = [...fragments].sort(() => 0.5 - Math.sin(item.id?.charCodeAt(0) || 0) * 0.5);

                        return (
                            <>
                                {/* Section header bar */}
                                <div style={{
                                    backgroundColor: 'var(--anthropic-dark)', color: 'var(--anthropic-cream)', padding: '0.6rem 1rem',
                                    borderRadius: '8px 8px 0 0', fontSize: '0.75rem', fontWeight: 600, letterSpacing: '0.03em',
                                    fontFamily: 'var(--font-heading)'
                                }}>
                                    TOEFL 2026 — Writing Section: Build a Sentence
                                </div>
                                <div style={{
                                    border: '1px solid var(--anthropic-light-gray)', borderTop: 'none',
                                    borderRadius: '0 0 8px 8px', padding: '1.5rem', backgroundColor: 'var(--card-bg)',
                                }}>
                                    {/* Context hint */}
                                    {context && (
                                        <p style={{ fontSize: '0.8rem', color: '#6b7280', marginBottom: '1rem', fontStyle: 'italic' }}>
                                            {context}
                                        </p>
                                    )}

                                    {/* Instruction */}
                                    <p style={{ fontSize: '0.9rem', fontWeight: 500, marginBottom: '1rem', color: '#334155' }}>
                                        Arrange the words to form a correct sentence.
                                    </p>

                                    {/* Word Bank */}
                                    <div style={{ marginBottom: '0.5rem' }}>
                                        <span style={{ fontSize: '0.7rem', fontWeight: 600, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Word Bank</span>
                                    </div>
                                    <div style={{
                                        display: 'flex', flexWrap: 'wrap', gap: '8px',
                                        padding: '12px', backgroundColor: '#f1f5f9', borderRadius: '8px',
                                        minHeight: '48px', marginBottom: '1.25rem', border: '1px dashed #cbd5e1',
                                    }}>
                                        {shuffled.map((word, i) => (
                                            <span key={i} style={{
                                                display: 'inline-block', padding: '8px 14px',
                                                backgroundColor: 'white', border: '1px solid #d1d5db',
                                                borderRadius: '6px', fontSize: '0.9rem', fontWeight: 400,
                                                cursor: 'grab', userSelect: 'none',
                                                boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                                                transition: 'all 0.15s',
                                            }}>
                                                {word}
                                            </span>
                                        ))}
                                    </div>

                                    {/* Answer Area — shows correct answer */}
                                    <div style={{ marginBottom: '0.5rem' }}>
                                        <span style={{ fontSize: '0.7rem', fontWeight: 600, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Correct Answer</span>
                                    </div>
                                    <div style={{
                                        display: 'flex', flexWrap: 'wrap', gap: '6px 10px', alignItems: 'center',
                                        padding: '14px 16px', border: '2px solid #10b981',
                                        borderRadius: '8px', backgroundColor: '#ecfdf5', minHeight: '48px',
                                    }}>
                                        {correctFragments.map((word, i) => (
                                            <span key={i} style={{
                                                display: 'inline-block', padding: '8px 14px',
                                                backgroundColor: 'white', border: '1px solid #86efac',
                                                borderRadius: '6px', fontSize: '0.9rem', fontWeight: 500,
                                                color: '#166534',
                                            }}>
                                                {word}
                                            </span>
                                        ))}
                                    </div>

                                    {/* Correct sentence as text */}
                                    <div style={{
                                        marginTop: '1rem', padding: '0.75rem 1rem',
                                        backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '6px',
                                    }}>
                                        <span style={{ fontSize: '0.7rem', fontWeight: 600, color: '#15803d', marginRight: '0.5rem' }}>✓</span>
                                        <span style={{ fontSize: '0.9rem', color: 'var(--anthropic-sage)', fontFamily: 'var(--font-body)' }}>
                                            {correctFragments.join(' ')}
                                        </span>
                                    </div>
                                </div>
                            </>
                        );
                    })() : parsedContent.type === 'Write for Academic Discussion' ? (
                        /* ─── WRITE FOR ACADEMIC DISCUSSION PREVIEW ─── */
                        <>
                            <div style={{
                                backgroundColor: 'var(--anthropic-dark)', color: 'var(--anthropic-cream)', padding: '0.6rem 1rem',
                                borderRadius: '8px 8px 0 0', fontSize: '0.75rem', fontWeight: 600, letterSpacing: '0.03em',
                                fontFamily: 'var(--font-heading)'
                            }}>
                                TOEFL 2026 — Writing Section: Academic Discussion
                            </div>
                            <div style={{
                                border: '1px solid var(--anthropic-light-gray)', borderTop: 'none',
                                borderRadius: '0 0 8px 8px', backgroundColor: 'var(--card-bg)',
                                display: 'flex', flexDirection: 'column', height: '600px',
                            }}>
                                {/* Top Layout: Instructions and Timeline */}
                                <div style={{
                                    padding: '1rem 1.5rem',
                                    borderBottom: '1px solid #e2e8f0',
                                    backgroundColor: 'white',
                                    fontSize: '0.9rem',
                                    color: '#334155'
                                }}>
                                    <p style={{ fontWeight: 600, marginBottom: '0.5rem' }}>
                                        Your professor is teaching a class on <strong>{parsedContent.title}</strong>. Write a post responding to the professor's question.
                                    </p>
                                    <ul style={{ margin: 0, paddingLeft: '1.5rem', color: '#64748b', fontSize: '0.85rem' }}>
                                        <li>Express and support your opinion</li>
                                        <li>Make a contribution to the discussion</li>
                                        <li>An effective response will contain <strong>at least 100 words</strong>.</li>
                                    </ul>
                                </div>

                                {/* Main Content Split */}
                                <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>

                                    {/* Left Panel: Discussion Board */}
                                    <div style={{
                                        flex: 6,
                                        padding: '1.5rem',
                                        overflowY: 'auto',
                                        borderRight: '1px solid #e2e8f0',
                                        backgroundColor: '#f8fafc'
                                    }}>

                                        {/* Professor Post */}
                                        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem' }}>
                                            <div style={{ width: '40px', height: '40px', borderRadius: '50%', backgroundColor: 'var(--anthropic-dark)', color: 'var(--anthropic-cream)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', flexShrink: 0 }}>
                                                P
                                            </div>
                                            <div style={{ flex: 1 }}>
                                                <div style={{ fontWeight: 600, color: '#1e293b', marginBottom: '0.25rem', fontSize: '0.9rem' }}>Professor</div>
                                                <div style={{
                                                    backgroundColor: 'white',
                                                    padding: '1rem',
                                                    borderRadius: '0 8px 8px 8px',
                                                    border: '1px solid #e2e8f0',
                                                    boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                                                    fontSize: '0.95rem',
                                                    lineHeight: 1.6,
                                                    color: '#334155'
                                                }}>
                                                    {rawContent.professor_prompt || parsedContent.text}
                                                </div>
                                            </div>
                                        </div>

                                        {/* Student 1 Post */}
                                        {(rawContent.student_1_name || rawContent.studentA) && (
                                            <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem' }}>
                                                <div style={{ width: '40px', height: '40px', borderRadius: '50%', backgroundColor: '#10b981', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', flexShrink: 0 }}>
                                                    {(rawContent.student_1_name || rawContent.studentA?.name || 'S').charAt(0).toUpperCase()}
                                                </div>
                                                <div style={{ flex: 1 }}>
                                                    <div style={{ fontWeight: 600, color: '#1e293b', marginBottom: '0.25rem', fontSize: '0.9rem' }}>
                                                        {rawContent.student_1_name || rawContent.studentA?.name || 'Student 1'}
                                                    </div>
                                                    <div style={{
                                                        backgroundColor: 'white',
                                                        padding: '1rem',
                                                        borderRadius: '0 8px 8px 8px',
                                                        border: '1px solid #e2e8f0',
                                                        boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                                                        fontSize: '0.95rem',
                                                        lineHeight: 1.6,
                                                        color: '#475569'
                                                    }}>
                                                        {rawContent.student_1_response || rawContent.studentA?.text || rawContent.studentA?.opinion}
                                                    </div>
                                                </div>
                                            </div>
                                        )}

                                        {/* Student 2 Post */}
                                        {(rawContent.student_2_name || rawContent.studentB) && (
                                            <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem' }}>
                                                <div style={{ width: '40px', height: '40px', borderRadius: '50%', backgroundColor: '#8b5cf6', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', flexShrink: 0 }}>
                                                    {(rawContent.student_2_name || rawContent.studentB?.name || 'S').charAt(0).toUpperCase()}
                                                </div>
                                                <div style={{ flex: 1 }}>
                                                    <div style={{ fontWeight: 600, color: '#1e293b', marginBottom: '0.25rem', fontSize: '0.9rem' }}>
                                                        {rawContent.student_2_name || rawContent.studentB?.name || 'Student 2'}
                                                    </div>
                                                    <div style={{
                                                        backgroundColor: 'white',
                                                        padding: '1rem',
                                                        borderRadius: '0 8px 8px 8px',
                                                        border: '1px solid #e2e8f0',
                                                        boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                                                        fontSize: '0.95rem',
                                                        lineHeight: 1.6,
                                                        color: '#475569'
                                                    }}>
                                                        {rawContent.student_2_response || rawContent.studentB?.text || rawContent.studentB?.opinion}
                                                    </div>
                                                </div>
                                            </div>
                                        )}

                                    </div>

                                    {/* Right Panel: Student Input */}
                                    <div style={{ flex: 4, display: 'flex', flexDirection: 'column', backgroundColor: 'white' }}>
                                        <div style={{
                                            padding: '0.75rem 1rem',
                                            backgroundColor: '#f1f5f9',
                                            borderBottom: '1px solid #e2e8f0',
                                            display: 'flex',
                                            gap: '0.5rem'
                                        }}>
                                            <Button variant="secondary" size="sm" style={{ backgroundColor: 'white' }} disabled>Cut</Button>
                                            <Button variant="secondary" size="sm" style={{ backgroundColor: 'white' }} disabled>Paste</Button>
                                            <Button variant="secondary" size="sm" style={{ backgroundColor: 'white' }} disabled>Undo</Button>
                                            <div style={{ marginLeft: 'auto', fontSize: '0.8rem', color: '#64748b', display: 'flex', alignItems: 'center' }}>
                                                Word Count: 0
                                            </div>
                                        </div>
                                        <textarea
                                            disabled
                                            placeholder="The student's response will be typed here..."
                                            style={{
                                                flex: 1,
                                                width: '100%',
                                                padding: '1rem',
                                                border: 'none',
                                                resize: 'none',
                                                fontSize: '0.95rem',
                                                lineHeight: 1.6,
                                                fontFamily: 'var(--font-ui)',
                                                color: '#334155',
                                                backgroundColor: '#fafaf9'
                                            }}
                                        />
                                    </div>
                                </div>
                            </div>
                        </>
                    ) : parsedContent.type === 'Listen and Repeat' ? (
                        /* ─── LISTEN AND REPEAT PREVIEW ─── */
                        <>
                            <div style={{
                                backgroundColor: 'var(--anthropic-dark)', color: 'var(--anthropic-cream)', padding: '0.75rem 1.25rem',
                                borderRadius: '8px 8px 0 0', fontSize: '0.85rem', fontWeight: 600,
                                letterSpacing: '0.02em', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                fontFamily: 'var(--font-heading)'
                            }}>
                                <span>TOEFL 2026 — Speaking Section: Listen and Repeat</span>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', fontSize: '0.7rem', fontFamily: 'var(--font-body)' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                                        <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--anthropic-sage)' }}></div>
                                        <span>Mic Ready</span>
                                    </div>
                                    <span>System Audio: OK</span>
                                </div>
                            </div>
                            <div style={{
                                border: '1px solid var(--anthropic-light-gray)', borderTop: 'none',
                                borderRadius: '0 0 8px 8px', backgroundColor: 'var(--card-bg)',
                                display: 'flex', flexDirection: 'column', minHeight: '400px',
                            }}>
                                <div style={{ padding: '1.5rem', borderBottom: '1px solid #eef2f6', backgroundColor: 'white' }}>
                                    <p style={{ fontSize: '1rem', color: '#1e293b', fontWeight: 500 }}>
                                        Instructions: Listen to each sentence and repeat it exactly as you hear it.
                                    </p>
                                </div>
                                <div style={{ padding: '1.5rem', flex: 1, backgroundColor: '#fdfaff' }}>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                                        {(rawContent.sentences || []).map((s: any, i: number) => (
                                            <div key={i} style={{
                                                backgroundColor: 'white', border: '1px solid #ddd6fe',
                                                borderRadius: '10px', padding: '1.25rem', display: 'flex',
                                                justifyContent: 'space-between', alignItems: 'center',
                                                boxShadow: '0 2px 4px rgba(124, 58, 237, 0.05)',
                                                transition: 'all 0.2s'
                                            }}>
                                                <div style={{ display: 'flex', gap: '1.25rem', alignItems: 'center' }}>
                                                    <div style={{
                                                        width: '32px', height: '32px', borderRadius: '50%',
                                                        backgroundColor: '#f5f3ff', display: 'flex', alignItems: 'center',
                                                        justifyContent: 'center', fontSize: '0.9rem', fontWeight: 700, color: '#7c3aed', fontFamily: 'var(--font-ui)'
                                                    }}>
                                                        {i + 1}
                                                    </div>
                                                    <span style={{ fontSize: '1rem', color: '#1e293b', fontWeight: 500, fontFamily: 'var(--font-body)' }}>{typeof s === 'string' ? s : s.text}</span>
                                                </div>
                                                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                                                    <audio controls src={(() => { const url = s.audioUrl || s.audio_url || s.audio_file; if (!url) return undefined; return url.startsWith('http') || url.startsWith('/') ? url : `/${url}`; })()} style={{ height: '32px', width: '220px' }} />
                                                    <div style={{
                                                        padding: '0.4rem 0.8rem', borderRadius: '6px',
                                                        backgroundColor: '#7c3aed', color: 'white',
                                                        fontSize: '0.7rem', fontWeight: 700, cursor: 'pointer',
                                                        textTransform: 'uppercase', letterSpacing: '0.05em', fontFamily: 'var(--font-ui)'
                                                    }}>
                                                        🎤 Repeat
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </>
                    ) : parsedContent.type === 'Listen and Choose a Response' ? (
                        /* ─── LISTEN AND CHOOSE A RESPONSE PREVIEW ─── */
                        <>
                            <div style={{
                                backgroundColor: 'var(--anthropic-dark)', color: 'var(--anthropic-cream)', padding: '0.75rem 1.25rem',
                                borderRadius: '8px 8px 0 0', fontSize: '0.85rem', fontWeight: 600,
                                letterSpacing: '0.02em', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                fontFamily: 'var(--font-heading)'
                            }}>
                                <span>TOEFL 2026 — Listening Section: Listen and Choose a Response</span>
                                <div style={{ fontSize: '0.7rem', opacity: 0.9, fontFamily: 'var(--font-body)' }}>Question 1 of 1</div>
                            </div>
                            <div style={{
                                border: '1px solid var(--anthropic-light-gray)', borderTop: 'none',
                                borderRadius: '0 0 8px 8px', backgroundColor: 'var(--card-bg)',
                                display: 'flex', flexDirection: 'column', minHeight: '450px',
                            }}>
                                <div style={{ padding: '2rem', flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center' }}>
                                    <div style={{
                                        width: '80px', height: '80px', borderRadius: '50%',
                                        backgroundColor: '#ecfdf5', border: '2px solid #059669',
                                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                                        fontSize: '2.5rem', color: '#059669', marginBottom: '1.5rem',
                                        boxShadow: '0 0 20px rgba(5, 150, 105, 0.1)'
                                    }}>
                                        🎧
                                    </div>
                                    <h3 style={{ fontSize: '1.25rem', fontWeight: 600, color: '#064e3b', marginBottom: '1rem' }}>Listen to the conversation</h3>
                                    <p style={{ color: '#065f46', maxWidth: '500px', lineHeight: 1.6, marginBottom: '2rem' }}>
                                        You will hear a short interaction. Listen carefully and then choose the most appropriate response from the options below.
                                    </p>

                                    {/* Main Audio for the task */}
                                    {parsedContent.audioUrl && (
                                        <div style={{
                                            backgroundColor: 'white', padding: '1rem 2rem',
                                            borderRadius: '50px', border: '1px solid #10b981',
                                            boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
                                            marginBottom: '2.5rem'
                                        }}>
                                            <audio controls src={parsedContent.audioUrl.startsWith('http') ? parsedContent.audioUrl : `/${parsedContent.audioUrl}`} style={{ height: '40px', width: '300px' }} />
                                        </div>
                                    )}

                                    {/* Questions Container */}
                                    <div style={{ width: '100%', maxWidth: '600px', textAlign: 'left' }}>
                                        {parsedContent.questions.map((q, i) => (
                                            <div key={i} style={{ backgroundColor: 'white', borderRadius: '12px', padding: '1.5rem', border: '1px solid #d1fae5', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)' }}>
                                                <p style={{ fontWeight: 600, color: '#064e3b', fontSize: '1.05rem', marginBottom: '1.25rem' }}>{q.text || "Choose the best response:"}</p>
                                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                                    {q.options.map((opt, oi) => (
                                                        <div key={oi} style={{
                                                            padding: '0.85rem 1rem', borderRadius: '8px',
                                                            border: '1.2px solid',
                                                            borderColor: q.correct_answer === oi ? '#10b981' : '#e2e8f0',
                                                            backgroundColor: q.correct_answer === oi ? '#f0fdf4' : 'white',
                                                            display: 'flex', alignItems: 'center', gap: '0.75rem',
                                                            fontSize: '0.95rem', color: '#374151'
                                                        }}>
                                                            <div style={{
                                                                width: '24px', height: '24px', borderRadius: '50%',
                                                                border: '1.5px solid',
                                                                borderColor: q.correct_answer === oi ? '#10b981' : '#d1d5db',
                                                                backgroundColor: q.correct_answer === oi ? '#10b981' : 'transparent',
                                                                color: q.correct_answer === oi ? 'white' : '#6b7280',
                                                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                                fontSize: '0.75rem', fontWeight: 700
                                                            }}>
                                                                {String.fromCharCode(65 + oi)}
                                                            </div>
                                                            <span style={{ fontWeight: q.correct_answer === oi ? 600 : 400 }}>{opt}</span>
                                                            {q.correct_answer === oi && <span style={{ marginLeft: 'auto', fontSize: '0.7rem', color: '#059669', fontWeight: 700 }}>CORRECT RESPONSE</span>}
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </>
                    ) : parsedContent.type === 'Take an Interview' ? (
                        /* ─── TAKE AN INTERVIEW PREVIEW ─── */
                        <>
                            <div style={{
                                backgroundColor: 'var(--anthropic-dark)', color: 'var(--anthropic-cream)', padding: '0.75rem 1.25rem',
                                borderRadius: '8px 8px 0 0', fontSize: '0.85rem', fontWeight: 600,
                                letterSpacing: '0.02em', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                fontFamily: 'var(--font-heading)'
                            }}>
                                <span>TOEFL 2026 — Speaking Section: Take an Interview</span>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', fontSize: '0.7rem', fontFamily: 'var(--font-body)' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                                        <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--anthropic-sage)' }}></div>
                                        <span>System Ready</span>
                                    </div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                                        <span>🔊</span>
                                        <div style={{ width: '60px', height: '4px', backgroundColor: 'rgba(255,255,255,0.3)', borderRadius: '2px' }}>
                                            <div style={{ width: '70%', height: '100%', backgroundColor: 'var(--anthropic-cream)', borderRadius: '2px' }}></div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div style={{
                                border: '1px solid var(--anthropic-light-gray)', borderTop: 'none',
                                borderRadius: '0 0 8px 8px', backgroundColor: 'var(--card-bg)',
                                display: 'flex', flexDirection: 'column', minHeight: '500px',
                            }}>
                                {/* Interviewer Intro Section */}
                                <div style={{
                                    padding: '2rem', borderBottom: '1px solid #eef2f6',
                                    display: 'flex', gap: '2rem', alignItems: 'flex-start',
                                    backgroundColor: 'white'
                                }}>
                                    <div style={{
                                        width: '120px', height: '120px', borderRadius: '12px',
                                        backgroundColor: '#f1f5f9', display: 'flex', alignItems: 'center',
                                        justifyContent: 'center', fontSize: '3rem', border: '1px solid #e2e8f0',
                                        flexShrink: 0, boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.05)'
                                    }}>
                                        👤
                                    </div>
                                    <div>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
                                            <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#004a99', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Interview Context</span>
                                            <div style={{ height: '1px', flex: 1, backgroundColor: '#e2e8f0' }}></div>
                                        </div>
                                        <p style={{ fontSize: '1.1rem', lineHeight: 1.6, color: '#1e293b', fontWeight: 500 }}>
                                            {parsedContent.text}
                                        </p>
                                        <div style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem' }}>
                                            <div style={{ padding: '0.5rem 1rem', backgroundColor: '#f0f7ff', border: '1px solid #bcd7f5', borderRadius: '6px', fontSize: '0.8rem', color: '#004a99', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                <span>⏱️</span> <strong>Total Questions:</strong> {parsedContent.questions.length}
                                            </div>
                                            <div style={{ padding: '0.5rem 1rem', backgroundColor: '#f0f7ff', border: '1px solid #bcd7f5', borderRadius: '6px', fontSize: '0.8rem', color: '#004a99', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                <span>🎤</span> <strong>Response Format:</strong> Spoken
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Questions List */}
                                <div style={{ padding: '1.5rem 2rem', backgroundColor: '#f8fafc', flex: 1 }}>
                                    <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#64748b', marginBottom: '1.5rem', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        <span>📋</span> Interview Questions
                                    </h4>

                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                                        {parsedContent.questions.map((q, i) => (
                                            <div key={i} style={{
                                                backgroundColor: 'white', borderRadius: '10px',
                                                border: '1px solid #e2e8f0', overflow: 'hidden',
                                                boxShadow: '0 2px 4px rgba(0,0,0,0.02)',
                                                transition: 'transform 0.2s, box-shadow 0.2s',
                                                cursor: 'default'
                                            }}
                                                onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.05)'; }}
                                                onMouseLeave={(e) => { e.currentTarget.style.transform = 'none'; e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.02)'; }}
                                            >
                                                <div style={{ display: 'flex', borderBottom: '1px solid #f1f5f9' }}>
                                                    <div style={{
                                                        width: '48px', backgroundColor: '#004a99', color: 'white',
                                                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                        fontSize: '1.1rem', fontWeight: 700
                                                    }}>
                                                        {i + 1}
                                                    </div>
                                                    <div style={{ flex: 1, padding: '1.25rem' }}>
                                                        <p style={{ fontSize: '0.95rem', lineHeight: 1.5, color: '#334155', fontWeight: 500, marginBottom: '1rem' }}>
                                                            {q.text}
                                                        </p>

                                                        {/* Question Controls */}
                                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                            <div style={{ display: 'flex', gap: '1rem' }}>
                                                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: '#64748b', fontSize: '0.75rem' }}>
                                                                    <span>⏱️</span> {q.timeLimit || 45}s Prep/Speak
                                                                </div>
                                                                {q.audioUrl && (
                                                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: '#10b981', fontSize: '0.75rem', fontWeight: 600 }}>
                                                                        <span>✓</span> Audio Linked
                                                                    </div>
                                                                )}
                                                            </div>
                                                            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                                                                {q.audioUrl ? (
                                                                    <audio
                                                                        controls
                                                                        src={q.audioUrl.startsWith('http') ? q.audioUrl : `/${q.audioUrl}`}
                                                                        style={{ height: '32px', width: '240px' }}
                                                                    />
                                                                ) : (
                                                                    <div style={{ fontSize: '0.7rem', color: '#94a3b8', fontStyle: 'italic', padding: '0.25rem 0.75rem', backgroundColor: '#f8fafc', borderRadius: '4px', border: '1px dashed #cbd5e1' }}>
                                                                        Audio expected/not found
                                                                    </div>
                                                                )}
                                                                <div style={{
                                                                    padding: '0.35rem 0.75rem', borderRadius: '4px',
                                                                    backgroundColor: '#fee2e2', color: '#dc2626',
                                                                    fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase'
                                                                }}>
                                                                    Recording Off
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </>
                    ) : parsedContent.type === 'Write an Email' ? (
                        /* ─── WRITE AN EMAIL PREVIEW ─── */
                        <>
                            <div style={{
                                backgroundColor: 'var(--anthropic-dark)', color: 'var(--anthropic-cream)', padding: '0.6rem 1rem',
                                borderRadius: '8px 8px 0 0', fontSize: '0.75rem', fontWeight: 600, letterSpacing: '0.03em',
                                fontFamily: 'var(--font-heading)'
                            }}>
                                TOEFL 2026 — Writing Section: Write an Email
                            </div>
                            <div style={{
                                border: '1px solid var(--anthropic-light-gray)', borderTop: 'none',
                                borderRadius: '0 0 8px 8px', backgroundColor: 'var(--card-bg)',
                                display: 'flex', flexDirection: 'column', height: '600px',
                            }}>
                                <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
                                    {/* Left Panel: Prompt */}
                                    <div style={{
                                        flex: 5,
                                        padding: '1.5rem',
                                        overflowY: 'auto',
                                        borderRight: '1px solid #e2e8f0',
                                        backgroundColor: 'white'
                                    }}>
                                        <div style={{ backgroundColor: '#f1f5f9', padding: '1.25rem', borderRadius: '8px', marginBottom: '1.5rem', borderLeft: '4px solid #3b82f6' }}>
                                            <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem', color: '#1e293b' }}>Scenario</h3>
                                            <p style={{ fontSize: '0.9rem', lineHeight: 1.6, color: '#334155', whiteSpace: 'pre-wrap' }}>
                                                {rawContent.scenario || rawContent.situation || rawContent.text || "Read the scenario..."}
                                            </p>
                                        </div>
                                        <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem', color: '#1e293b' }}>Task</h3>
                                        <p style={{ fontSize: '0.9rem', lineHeight: 1.6, color: '#334155', whiteSpace: 'pre-wrap' }}>
                                            {rawContent.task || rawContent.content || "Write an email responding to the situation."}
                                        </p>
                                        {Array.isArray(rawContent.bullets) && rawContent.bullets.length > 0 && (
                                            <ul style={{ paddingLeft: '1.5rem', marginTop: '0.75rem', fontSize: '0.9rem', lineHeight: 1.6, color: '#334155' }}>
                                                {rawContent.bullets.map((b: string, i: number) => (
                                                    <li key={i}>{b}</li>
                                                ))}
                                            </ul>
                                        )}
                                    </div>

                                    {/* Right Panel: Editor */}
                                    <div style={{ flex: 4, display: 'flex', flexDirection: 'column', backgroundColor: 'white' }}>
                                        <div style={{ padding: '1rem 1.5rem', borderBottom: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column', gap: '0.5rem', backgroundColor: '#f8fafc' }}>
                                            <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                                                <span style={{ fontWeight: 600, width: '60px', color: '#475569', fontSize: '0.9rem' }}>To:</span>
                                                <span style={{ backgroundColor: '#e2e8f0', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.85rem', color: '#334155' }}>
                                                    {rawContent.to || "recipient@university.edu"}
                                                </span>
                                            </div>
                                            <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                                                <span style={{ fontWeight: 600, width: '60px', color: '#475569', fontSize: '0.9rem' }}>Subject:</span>
                                                <span style={{ color: '#334155', fontSize: '0.9rem', fontWeight: 500 }}>
                                                    {rawContent.subject || parsedContent.title || "Subject"}
                                                </span>
                                            </div>
                                        </div>
                                        <div style={{ padding: '0.5rem 1rem', borderBottom: '1px solid #e2e8f0', display: 'flex', gap: '0.5rem', backgroundColor: '#f1f5f9' }}>
                                            <Button variant="secondary" size="sm" style={{ backgroundColor: 'white', padding: '0.25rem 0.75rem', fontSize: '0.75rem' }} disabled>Cut</Button>
                                            <Button variant="secondary" size="sm" style={{ backgroundColor: 'white', padding: '0.25rem 0.75rem', fontSize: '0.75rem' }} disabled>Paste</Button>
                                            <Button variant="secondary" size="sm" style={{ backgroundColor: 'white', padding: '0.25rem 0.75rem', fontSize: '0.75rem' }} disabled>Undo</Button>
                                            <div style={{ marginLeft: 'auto', fontSize: '0.8rem', color: '#64748b', display: 'flex', alignItems: 'center' }}>
                                                Word Count: 0
                                            </div>
                                        </div>
                                        <textarea
                                            disabled
                                            placeholder="The student's email response will be typed here..."
                                            style={{
                                                flex: 1,
                                                width: '100%',
                                                padding: '1.5rem',
                                                border: 'none',
                                                resize: 'none',
                                                fontSize: '0.95rem',
                                                lineHeight: 1.6,
                                                fontFamily: 'var(--font-ui)',
                                                color: '#334155',
                                                backgroundColor: '#fafaf9'
                                            }}
                                        />
                                    </div>
                                </div>
                            </div>
                        </>
                    ) : (
                        /* ─── STANDARD PASSAGE / QUESTIONS PREVIEW ─── */
                        <>
                            {(parsedContent.text || parsedContent.script) && (
                                <>
                                    <div style={{
                                        backgroundColor: colors.header, color: 'white', padding: '0.6rem 1rem',
                                        borderRadius: '8px 8px 0 0', fontSize: '0.75rem', fontWeight: 600, letterSpacing: '0.03em',
                                    }}>
                                        TOEFL 2026 — {sectionLabel} Section: {parsedContent.type}
                                    </div>
                                    <div style={{
                                        border: `1.5px solid ${colors.border}`, borderTop: 'none',
                                        borderRadius: '0 0 8px 8px', padding: '1.5rem', backgroundColor: colors.bg,
                                    }}>
                                        {isComplete ? (() => {
                                            const fullText = parsedContent.text;
                                            const firstSentence = fullText.match(/^[^.!?]+[.!?]/)?.[0] || '';
                                            const rest = fullText.slice(firstSentence.length);
                                            const words = rest.split(/(\s+)/);

                                            let isWordSecond = false;

                                            return (
                                                <p style={{ fontSize: '1rem', lineHeight: 1.8, fontFamily: 'var(--font-body)', color: 'var(--anthropic-dark)', whiteSpace: 'pre-wrap' }}>
                                                    <strong>{firstSentence}</strong>
                                                    {words.map((part, index) => {
                                                        if (!part.trim()) return <span key={index}>{part}</span>;

                                                        const suffixMatch = part.match(/[.,;:!?']+$/);
                                                        const suffix = suffixMatch ? suffixMatch[0] : '';
                                                        const word = part.replace(/[.,;:!?']+$/, '');

                                                        if (isWordSecond && word.length >= 2) {
                                                            isWordSecond = !isWordSecond;
                                                            const keepLen = Math.floor(word.length / 2);
                                                            const keep = word.slice(0, keepLen);
                                                            const gap = word.slice(keepLen);
                                                            return (
                                                                <span key={index} className="word-gap">
                                                                    {keep}
                                                                    <span style={{
                                                                        display: 'inline-block', borderBottom: '2px solid var(--anthropic-dark)',
                                                                        minWidth: `${gap.length * 9}px`, padding: '0 3px', margin: '0 2px',
                                                                        color: 'var(--anthropic-dark)', fontWeight: 600, fontFamily: 'var(--font-heading)'
                                                                    }}>{gap}</span>
                                                                    {suffix}
                                                                </span>
                                                            );
                                                        }

                                                        isWordSecond = !isWordSecond;
                                                        return <span key={index}>{part}</span>;
                                                    })}
                                                </p>
                                            );
                                        })() : (
                                            <>
                                                {/* Daily Life Header */}
                                                {(rawContent.from || rawContent.subject) && (
                                                    <div style={{
                                                        marginBottom: '1.5rem', padding: '1rem', backgroundColor: '#f0f9ff',
                                                        border: '1px solid #bae6fd', borderRadius: '8px', fontSize: '0.85rem'
                                                    }}>
                                                        {rawContent.from && <div style={{ marginBottom: '0.25rem' }}><strong>From:</strong> {rawContent.from}</div>}
                                                        {rawContent.to && <div style={{ marginBottom: '0.25rem' }}><strong>To:</strong> {rawContent.to}</div>}
                                                        {rawContent.date && <div style={{ marginBottom: '0.25rem' }}><strong>Date:</strong> {rawContent.date}</div>}
                                                        {rawContent.subject && <div><strong>Subject:</strong> {rawContent.subject}</div>}
                                                    </div>
                                                )}
                                                {parsedContent.text && (
                                                    <p style={{ fontSize: '1rem', lineHeight: 1.8, color: 'var(--anthropic-dark)', whiteSpace: 'pre-wrap', fontFamily: 'var(--font-body)' }}>
                                                        {parsedContent.text}
                                                    </p>
                                                )}
                                                {parsedContent.script && (
                                                    <div style={{ marginTop: parsedContent.text ? '1.5rem' : '0', padding: '1.25rem', backgroundColor: 'var(--anthropic-cream)', borderRadius: '8px', border: '1px solid var(--anthropic-light-gray)' }}>
                                                        <h4 style={{ fontFamily: 'var(--font-heading)', fontSize: '0.85rem', fontWeight: 600, color: 'var(--anthropic-dark)', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                                                            Listening Transcript
                                                        </h4>
                                                        <p style={{ fontSize: '0.95rem', lineHeight: 1.7, color: 'var(--anthropic-dark)', whiteSpace: 'pre-wrap', fontFamily: 'var(--font-body)' }}>
                                                            {parsedContent.script}
                                                        </p>
                                                    </div>
                                                )}
                                            </>
                                        )}
                                    </div>
                                </>
                            )}

                            {/* Hints for C-test */}
                            {isComplete && parsedContent.hints && parsedContent.hints.length > 0 && (
                                <div style={{ marginTop: '1.25rem', padding: '1.25rem', backgroundColor: 'var(--anthropic-cream)', borderRadius: '8px', border: '1px solid var(--anthropic-light-gray)' }}>
                                    <h4 style={{ fontFamily: 'var(--font-heading)', fontSize: '0.85rem', fontWeight: 600, color: 'var(--anthropic-dark)', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                                        Hints & Vocabulary
                                    </h4>
                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '0.75rem', fontFamily: 'var(--font-body)' }}>
                                        {parsedContent.hints.map((hint, hi) => (
                                            <div key={hi} style={{ fontSize: '0.85rem', color: 'var(--anthropic-dark)', display: 'flex', gap: '0.5rem' }}>
                                                <span style={{ fontWeight: 600, color: 'var(--text-muted)' }}>{hi + 1}.</span>
                                                <span>{hint}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Questions */}
                            {hasQuestions && (
                                <div style={{ marginTop: '1.25rem', fontFamily: 'var(--font-body)' }}>
                                    {parsedContent.questions.map((q, i) => (
                                        <div key={i} style={{ marginBottom: '1.25rem', padding: '1rem', backgroundColor: 'var(--card-bg)', borderRadius: '8px', border: '1px solid var(--anthropic-light-gray)' }}>
                                            <p style={{ fontWeight: 600, marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--anthropic-dark)' }}>
                                                {/^\d+\./.test(String(q.text).trim()) ? q.text : `${q.question_num}. ${q.text}`}
                                            </p>
                                            <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '0.5rem' }}>
                                                {q.audioUrl && (
                                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--anthropic-blue)', fontSize: '0.75rem', backgroundColor: 'rgba(106, 155, 204, 0.1)', padding: '0.2rem 0.5rem', borderRadius: '4px' }}>
                                                        🔊 Audio Available
                                                    </div>
                                                )}
                                                {q.timeLimit && (
                                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-muted)', fontSize: '0.75rem', backgroundColor: 'var(--anthropic-light-gray)', padding: '0.2rem 0.5rem', borderRadius: '4px' }}>
                                                        ⏱️ {q.timeLimit}s Response Time
                                                    </div>
                                                )}
                                            </div>
                                            {q.options.length > 0 && (
                                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem', paddingLeft: '0.5rem' }}>
                                                    {q.options.map((opt, oi) => (
                                                        <label key={oi} style={{
                                                            display: 'flex', alignItems: 'center', gap: '0.5rem',
                                                            padding: '0.35rem 0.5rem', borderRadius: '6px', fontSize: '0.85rem', color: 'var(--foreground)',
                                                            backgroundColor: q.correct_answer === oi ? 'rgba(120, 140, 93, 0.1)' : 'transparent',
                                                            border: q.correct_answer === oi ? '1px solid var(--anthropic-sage)' : '1px solid transparent',
                                                        }}>
                                                            <input type="radio" name={`modal-q${i}`} disabled checked={q.correct_answer === oi} />
                                                            <span style={{ fontWeight: q.correct_answer === oi ? 600 : 400 }}>
                                                                {String.fromCharCode(65 + oi)}. {opt}
                                                            </span>
                                                            {q.correct_answer === oi && <span style={{ fontSize: '0.7rem', color: 'var(--anthropic-sage)', marginLeft: 'auto', fontWeight: 600 }}>✓ Correct</span>}
                                                        </label>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}

                            {/* Fallback for items with no text and no questions */}
                            {!parsedContent.text && !parsedContent.script && !hasQuestions && (
                                <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>
                                    <p>Raw item data (no preview layout available for this item type)</p>
                                    <pre style={{ textAlign: 'left', fontSize: '0.75rem', marginTop: '1rem', backgroundColor: '#f8fafc', padding: '1rem', borderRadius: '8px', overflow: 'auto', maxHeight: '400px' }}>
                                        {JSON.stringify(rawContent, null, 2)}
                                    </pre>
                                </div>
                            )}
                        </>
                    )}
                </div>

                {/* History Section */}
                {showHistory && (
                    <div style={{
                        padding: '1.5rem',
                        borderTop: '2px solid #eef2f6',
                        backgroundColor: '#f8fafc',
                        animation: 'slideDown 0.3s ease-out'
                    }}>
                        <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem', color: '#1e293b', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <span>📋</span> Audit Trail & Review History
                        </h3>

                        {loadingHistory ? (
                            <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>Loading history...</div>
                        ) : (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                                {/* Review Logs */}
                                <div style={{ backgroundColor: 'white', borderRadius: '8px', border: '1px solid #e2e8f0', overflow: 'hidden' }}>
                                    <div style={{ padding: '0.75rem 1rem', backgroundColor: '#f1f5f9', borderBottom: '1px solid #e2e8f0', fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>
                                        QA REVIEW LOGS
                                    </div>
                                    <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                                        {history?.reviews && history.reviews.length > 0 ? (
                                            history.reviews.map((rev: any, idx: number) => (
                                                <div key={rev.id} style={{
                                                    padding: '1rem',
                                                    borderBottom: idx === history.reviews.length - 1 ? 'none' : '1px solid #f1f5f9',
                                                    display: 'flex',
                                                    gap: '1rem'
                                                }}>
                                                    <div style={{
                                                        width: '40px', height: '40px', borderRadius: '8px',
                                                        backgroundColor: rev.action === 'PASS' ? '#dcfce7' : rev.action === 'FAIL' ? '#fee2e2' : '#fef9c3',
                                                        display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0
                                                    }}>
                                                        <span style={{ fontSize: '1.2rem' }}>{rev.action === 'PASS' ? '✅' : rev.action === 'FAIL' ? '❌' : '⚠️'}</span>
                                                    </div>
                                                    <div style={{ flex: 1 }}>
                                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                                                            <span style={{ fontWeight: 600, fontSize: '0.9rem', color: '#1e293b' }}>{rev.stage_name}</span>
                                                            <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{rev.timestamp ? new Date(rev.timestamp).toLocaleString() : 'No date'}</span>
                                                        </div>
                                                        <div style={{ fontSize: '0.8rem', color: '#475569', marginBottom: '0.5rem' }}>
                                                            <strong>Reviewer:</strong> {rev.reviewer}
                                                        </div>
                                                        <div style={{
                                                            fontSize: '0.85rem', color: '#334155', padding: '0.75rem',
                                                            backgroundColor: '#f8fafc', borderRadius: '6px', border: '1px solid #eef2f6',
                                                            whiteSpace: 'pre-wrap'
                                                        }}>
                                                            {rev.notes || "No additional comments provided."}
                                                        </div>
                                                    </div>
                                                </div>
                                            ))
                                        ) : (
                                            <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8', fontSize: '0.85rem' }}>No review logs found for this item.</div>
                                        )}
                                    </div>
                                </div>

                                {/* Version History */}
                                <div style={{ backgroundColor: 'white', borderRadius: '8px', border: '1px solid #e2e8f0', overflow: 'hidden' }}>
                                    <div style={{ padding: '0.75rem 1rem', backgroundColor: '#f1f5f9', borderBottom: '1px solid #e2e8f0', fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>
                                        VERSION HISTORY
                                    </div>
                                    <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                                        {history?.versions && history.versions.length > 0 ? (
                                            history.versions.map((ver: any, idx: number) => (
                                                <div key={ver.id} style={{
                                                    padding: '1rem',
                                                    borderBottom: idx === history.versions.length - 1 ? 'none' : '1px solid #f1f5f9',
                                                    display: 'flex',
                                                    gap: '1rem',
                                                    alignItems: 'center'
                                                }}>
                                                    <div style={{
                                                        width: '40px', height: '40px', borderRadius: '50%',
                                                        backgroundColor: '#eef2ff', color: '#6366f1',
                                                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                        fontWeight: 700, fontSize: '0.9rem', flexShrink: 0
                                                    }}>
                                                        v{ver.version_number}
                                                    </div>
                                                    <div style={{ flex: 1 }}>
                                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                                                            <span style={{ fontWeight: 600, fontSize: '0.9rem', color: '#1e293b' }}>Modified by {ver.changed_by}</span>
                                                            <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{new Date(ver.timestamp).toLocaleString()}</span>
                                                        </div>
                                                        <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
                                                            Snapshot of previous content saved.
                                                        </div>
                                                    </div>
                                                    <Button variant="secondary" size="sm" onClick={() => {
                                                        const win = window.open('', '_blank');
                                                        win?.document.write(`<pre>${JSON.stringify(JSON.parse(ver.prompt_content), null, 2)}</pre>`);
                                                    }}>View Snapshot</Button>
                                                </div>
                                            ))
                                        ) : (
                                            <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8', fontSize: '0.85rem' }}>This is the first version of this item.</div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Modal Footer */}
                <div style={{
                    padding: '1rem 1.5rem', borderTop: '1px solid #e2e8f0',
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    backgroundColor: '#f8fafc', borderRadius: '0 0 12px 12px',
                }}>
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                        ID: {item.id?.slice(0, 8)}... • Created: {item.created_at ? new Date(item.created_at).toLocaleDateString() : '—'}
                        {item.exposure_count !== undefined && ` • Exposures: ${item.exposure_count}`}
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <Button variant="ghost" size="sm" onClick={onClose}>Close</Button>
                        <Button size="sm" onClick={() => window.location.href = `/dashboard/admin/items/${item.id}/edit`}>✏️ Edit Item</Button>
                    </div>
                </div>
            </div>
        </div>
    );
}
// ─── OPTIMIZED ITEM ROW ───
const TestItemRow = memo(({
    item,
    index,
    totalCount,
    openPreview,
    handleSingleQA,
    router,
    getStatusBadge
}: {
    item: any;
    index: number;
    totalCount: number;
    openPreview: (item: any) => void;
    handleSingleQA: (id: string) => void;
    router: any;
    getStatusBadge: (status: string) => React.ReactNode;
}) => {
    const normalized = item._normalized;
    const title = item._displayTitle;

    return (
        <div style={{
            display: 'grid', gridTemplateColumns: '1.8fr 0.7fr 1.1fr 0.5fr 0.6fr 0.35fr 0.8fr 0.5fr 0.6fr 1fr', gap: '0.5rem',
            padding: '0.85rem 1.5rem',
            borderBottom: index === totalCount - 1 ? 'none' : '1px solid var(--border-color)',
            alignItems: 'center',
            backgroundColor: 'var(--card-bg)',
            transition: 'background-color 0.15s',
            fontFamily: 'var(--font-body)'
        }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                <div
                    onClick={() => openPreview(item)}
                    style={{ fontWeight: 600, color: 'var(--foreground)', fontSize: '0.85rem', cursor: 'pointer', transition: 'color 0.15s' }}
                    onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--anthropic-blue)')}
                    onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--foreground)')}
                    title="Click to preview"
                >
                    {title}
                </div>
                {item.generation_notes && (
                    <div style={{ fontSize: '0.7rem', color: item.lifecycle_status === 'REVIEW' || item.lifecycle_status === 'SUSPENDED' ? 'var(--anthropic-terracotta)' : 'var(--text-muted)' }}>
                        {item.generation_notes}
                    </div>
                )}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--foreground)' }}>{item.section}</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{normalized.type}</div>
            <div style={{ fontSize: '0.75rem', fontWeight: 500, color: 'var(--foreground)' }}>{item.target_level}</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{item.irt_difficulty}</div>
            <div style={{ fontSize: '0.65rem', fontWeight: 600, color: 'var(--anthropic-blue)', backgroundColor: 'rgba(106, 155, 204, 0.1)', borderRadius: '4px', padding: '0.1rem 0.35rem', textAlign: 'center', width: 'fit-content' }}>v{item.version || 1}</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{item.generated_by_model || '—'}</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{getItemAge(item.created_at)}</div>
            <div>{getStatusBadge(item.lifecycle_status)}</div>
            <div style={{ textAlign: 'right', display: 'flex', gap: '0.4rem', justifyContent: 'flex-end' }}>
                <Button variant="ghost" size="sm" onClick={() => router.push(`/dashboard/admin/items/${item.id}/edit`)}>Edit</Button>
                <Button variant="secondary" size="sm" onClick={() => handleSingleQA(item.id)}>QA</Button>
            </div>
        </div>
    );
});

TestItemRow.displayName = 'TestItemRow';

// ─── MAIN DASHBOARD ───
export default function ItemBankDashboard() {
    const { t } = useLanguage();
    const router = useRouter();
    const [searchTerm, setSearchTerm] = useState('');
    const [sectionFilter, setSectionFilter] = useState('All');
    const [typeFilter, setTypeFilter] = useState('All');
    const [statusFilter, setStatusFilter] = useState('All');
    const [previewItem, setPreviewItem] = useState<any>(null);
    const [previewContent, setPreviewContent] = useState<ParsedContent | null>(null);

    const [rawItems, setRawItems] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [isActionRunning, setIsActionRunning] = useState(false);
    const [actionMessage, setActionMessage] = useState('');

    const fetchItems = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/api/items`, {
                headers: {
                    'Bypass-Tunnel-Reminder': 'true'
                }
            });
            if (res.ok) {
                const data = await res.json();
                setRawItems(data);
            } else {
                const errText = await res.text();
                console.error("API Error:", res.status, errText);
            }
        } catch (error: any) {
            console.error("Failed to fetch items:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchItems();
    }, []);

    // Memoize pre-processed items to avoid expensive operations during render
    const processedItems = useMemo(() => {
        return rawItems.map(item => {
            const rawContent = typeof item.prompt_content === 'string' ? JSON.parse(item.prompt_content) : item.prompt_content;
            const normalized = normaliseContent(rawContent, item);

            let displayTitle = normalized.title;
            if ((displayTitle === 'Untitled Item' || displayTitle === rawContent.id)
                && Array.isArray(rawContent.fragments) && rawContent.fragments.length > 0) {
                const f = [...rawContent.fragments];
                f[0] = f[0].charAt(0).toUpperCase() + f[0].slice(1);
                displayTitle = f.join(' ') + (rawContent.endPunctuation || '.');
            }

            return {
                ...item,
                _normalized: normalized,
                _displayTitle: displayTitle,
                _searchable: `${displayTitle} ${item.id} ${item.section} ${item.task_type}`.toLowerCase()
            };
        });
    }, [rawItems]);

    // Memoize filtered items
    const filteredItems = useMemo(() => {
        const term = searchTerm.toLowerCase();
        return processedItems.filter(item => {
            // Search
            if (term && !item._searchable.includes(term)) {
                return false;
            }

            // Section filter
            if (sectionFilter !== 'All' && item.section !== sectionFilter.toUpperCase()) {
                return false;
            }

            // Type filter
            if (typeFilter !== 'All' && item.task_type !== typeFilter) {
                return false;
            }

            // Status filter
            if (statusFilter !== 'All' && item.lifecycle_status !== statusFilter) {
                return false;
            }

            return true;
        });
    }, [processedItems, searchTerm, sectionFilter, typeFilter, statusFilter]);

    const handleRunQA = async () => {
        setIsActionRunning(true);
        setActionMessage("Running QA + Auto-Remediation on all DRAFT & REVIEW items...");
        try {
            const res = await fetch(`${API_BASE_URL}/api/items/qa-pipeline`, {
                method: 'POST',
                headers: { 'Bypass-Tunnel-Reminder': 'true' }
            });
            if (res.ok) {
                const data = await res.json();
                const passed = data.results?.filter((r: any) => r.status === 'Passed').length || 0;
                const remediated = data.results?.filter((r: any) => r.status === 'Remediated').length || 0;
                const failed = data.results?.filter((r: any) => r.status === 'Failed').length || 0;
                setActionMessage(`Pipeline complete! ✅ ${passed} passed, 🔧 ${remediated} auto-fixed, ❌ ${failed} need review.`);
                fetchItems();
            } else {
                setActionMessage("Pipeline API Error");
            }
        } catch (error) {
            setActionMessage("Failed to run QA Pipeline");
        } finally {
            setTimeout(() => {
                setIsActionRunning(false);
                setActionMessage('');
            }, 4000);
        }
    };

    const handleSingleQA = async (itemId: string) => {
        setIsActionRunning(true);
        setActionMessage(`Running QA on item ${itemId.slice(0, 8)}...`);
        try {
            const res = await fetch(`${API_BASE_URL}/api/items/${itemId}/qa`, {
                method: 'POST',
                headers: { 'Bypass-Tunnel-Reminder': 'true' }
            });
            if (res.ok) {
                const data = await res.json();
                const r = data.result;
                setActionMessage(`Item ${itemId.slice(0, 8)}… → ${r?.status}: ${r?.reason}`);
                fetchItems();
            } else {
                setActionMessage("Single-item QA API Error");
            }
        } catch (error) {
            setActionMessage("Failed to run single-item QA");
        } finally {
            setTimeout(() => {
                setIsActionRunning(false);
                setActionMessage('');
            }, 4000);
        }
    };

    const handleSimulate = async () => {
        setIsActionRunning(true);
        setActionMessage("Running Psychometric IRT Simulations...");
        try {
            const res = await fetch(`${API_BASE_URL}/api/items/simulate-field-test`, {
                method: 'POST',
                headers: { 'Bypass-Tunnel-Reminder': 'true' }
            });
            if (res.ok) {
                const data = await res.json();
                setActionMessage(`Simulation complete! Generated data for ${data.results?.length || 0} items.`);
                fetchItems();
            } else {
                setActionMessage("Simulation API Error");
            }
        } catch (error) {
            setActionMessage("Failed to run Simulation");
        } finally {
            setTimeout(() => {
                setIsActionRunning(false);
                setActionMessage('');
            }, 3000);
        }
    };

    // ─── FILTERING CONSTANTS ───
    const sectionTaskTypes: Record<string, string[]> = {
        'Reading': ['READ_ACADEMIC_PASSAGE', 'READ_IN_DAILY_LIFE', 'COMPLETE_THE_WORDS'],
        'Listening': ['LISTEN_CHOOSE_RESPONSE', 'LISTEN_ACADEMIC_TALK', 'LISTEN_ANNOUNCEMENT', 'LISTEN_CONVERSATION'],
        'Speaking': ['LISTEN_AND_REPEAT', 'TAKE_AN_INTERVIEW'],
        'Writing': ['BUILD_A_SENTENCE', 'WRITE_ACADEMIC_DISCUSSION', 'WRITE_AN_EMAIL'],
    };

    const openPreview = (item: any) => {
        const parsed = typeof item.prompt_content === 'string' ? JSON.parse(item.prompt_content) : item.prompt_content;
        setPreviewItem(item);
        setPreviewContent(parsed);
    };

    const getStatusBadge = (status: string) => {
        const styles: Record<string, { bg: string, color: string, border: string }> = {
            'ACTIVE': { bg: 'rgba(120, 140, 93, 0.1)', color: 'var(--anthropic-sage)', border: 'var(--anthropic-sage)' },
            'DRAFT': { bg: 'var(--anthropic-light-gray)', color: 'var(--anthropic-dark)', border: 'var(--anthropic-mid-gray)' },
            'REVIEW': { bg: 'rgba(106, 155, 204, 0.1)', color: 'var(--anthropic-blue)', border: 'var(--anthropic-blue)' },
            'FIELD_TEST': { bg: 'var(--card-bg)', color: 'var(--text-muted)', border: 'var(--anthropic-mid-gray)' },
            'SUSPENDED': { bg: '#fee2e2', color: 'var(--anthropic-terracotta)', border: 'var(--anthropic-terracotta)' },
            'EXPOSED': { bg: 'rgba(217, 119, 87, 0.1)', color: 'var(--anthropic-terracotta)', border: 'var(--anthropic-terracotta)' },
            'ARCHIVED': { bg: 'var(--background)', color: 'var(--text-muted)', border: 'var(--border-color)' }
        };
        const currentStyle = styles[status] || styles['DRAFT'];
        return (
            <span style={{
                backgroundColor: currentStyle.bg, color: currentStyle.color,
                padding: '0.15rem 0.5rem', borderRadius: '4px', fontSize: '0.65rem', fontWeight: 600,
                border: `1px solid ${currentStyle.border}`, textTransform: 'uppercase', fontFamily: 'var(--font-heading)'
            }}>
                {status.replace('_', ' ')}
            </span>
        );
    };

    const selectStyle: React.CSSProperties = {
        height: '2.5rem', borderRadius: '6px', border: '1px solid var(--border-color)',
        padding: '0 0.75rem', backgroundColor: 'var(--card-bg)', fontSize: '0.875rem', cursor: 'pointer',
    };

    return (
        <div className="app-layout" style={{ backgroundColor: 'var(--background)' }}>
            {/* ─── PREVIEW MODAL ─── */}
            {previewItem && previewContent && (
                <PreviewModal item={previewItem} parsedContent={previewContent} onClose={() => { setPreviewItem(null); setPreviewContent(null); }} />
            )}

            {/* ─── ACTION RUNNING OVERLAY ─── */}
            {isActionRunning && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    backgroundColor: 'rgba(255, 255, 255, 0.8)',
                    backdropFilter: 'blur(4px)',
                    zIndex: 9999, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center'
                }}>
                    <div style={{
                        width: '50px', height: '50px',
                        border: '4px solid #f3f3f3', borderTop: '4px solid #3b82f6',
                        borderRadius: '50%', animation: 'spin 1s linear infinite'
                    }} />
                    <h3 style={{ marginTop: '1.5rem', fontSize: '1.2rem', fontWeight: 600, color: '#1e293b' }}>
                        {actionMessage}
                    </h3>
                    <style>{`
                        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
                    `}</style>
                </div>
            )}

            <header style={{ padding: '1rem 2rem', borderBottom: '1px solid var(--border-color)', backgroundColor: 'var(--card-bg)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{ width: '32px', height: '32px', backgroundColor: '#ef4444', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 'bold' }}>A</div>
                    <span style={{ fontWeight: 600, fontSize: '1.25rem' }}>{t('admin.manageItemsTitle')}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <LanguageSwitcher />
                    <span style={{ fontSize: '0.8rem', color: '#64748b' }}>{filteredItems.length} of {rawItems.length} items</span>
                    <span style={{ fontSize: '0.6rem', color: '#cbd5e1' }}>API: {API_BASE_URL}</span>
                    <Button variant="secondary" size="sm" onClick={handleRunQA}>Run QA Pipeline</Button>
                    <Button variant="secondary" size="sm" onClick={handleSimulate}>Simulate Field Test</Button>
                    <Button variant="ghost" size="sm" onClick={() => router.push('/dashboard/admin')}>{t('admin.back')}</Button>
                    <Button size="sm" onClick={() => router.push('/dashboard/admin/items/create')}>+ Create New Item</Button>
                </div>
            </header>

            <main className="container" style={{ paddingTop: '2rem', paddingBottom: '2rem', maxWidth: '1300px' }}>

                {/* ─── KPI OVERVIEW ─── */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '1rem', marginBottom: '2.5rem', fontFamily: 'var(--font-body)' }}>
                    {/* Draft */}
                    <div onClick={() => setStatusFilter('DRAFT')} style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', cursor: 'pointer', transition: 'transform 0.1s, border-color 0.2s' }} onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.borderColor = 'var(--text-muted)'; }} onMouseLeave={(e) => { e.currentTarget.style.transform = 'none'; e.currentTarget.style.borderColor = 'var(--border-color)'; }}>
                        <div style={{ fontFamily: 'var(--font-heading)', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Draft & Authoring</div>
                        <div style={{ fontSize: '1.8rem', fontWeight: 500, color: 'var(--foreground)' }}>{rawItems.filter(i => i.lifecycle_status === 'DRAFT').length}</div>
                    </div>
                    {/* Review */}
                    <div onClick={() => setStatusFilter('REVIEW')} style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', cursor: 'pointer', transition: 'transform 0.1s, border-color 0.2s' }} onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.borderColor = 'var(--text-muted)'; }} onMouseLeave={(e) => { e.currentTarget.style.transform = 'none'; e.currentTarget.style.borderColor = 'var(--border-color)'; }}>
                        <div style={{ fontFamily: 'var(--font-heading)', fontSize: '0.75rem', fontWeight: 600, color: 'var(--anthropic-blue)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>In QA Review</div>
                        <div style={{ fontSize: '1.8rem', fontWeight: 500, color: 'var(--anthropic-blue)' }}>{rawItems.filter(i => i.lifecycle_status === 'REVIEW').length}</div>
                    </div>
                    {/* Field Test */}
                    <div onClick={() => setStatusFilter('FIELD_TEST')} style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', cursor: 'pointer', transition: 'transform 0.1s, border-color 0.2s' }} onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.borderColor = 'var(--text-muted)'; }} onMouseLeave={(e) => { e.currentTarget.style.transform = 'none'; e.currentTarget.style.borderColor = 'var(--border-color)'; }}>
                        <div style={{ fontFamily: 'var(--font-heading)', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Field Test (IRT)</div>
                        <div style={{ fontSize: '1.8rem', fontWeight: 500, color: 'var(--foreground)' }}>{rawItems.filter(i => i.lifecycle_status === 'FIELD_TEST').length}</div>
                    </div>
                    {/* Active */}
                    <div onClick={() => setStatusFilter('ACTIVE')} style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', cursor: 'pointer', transition: 'transform 0.1s, border-color 0.2s' }} onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.borderColor = 'var(--text-muted)'; }} onMouseLeave={(e) => { e.currentTarget.style.transform = 'none'; e.currentTarget.style.borderColor = 'var(--border-color)'; }}>
                        <div style={{ fontFamily: 'var(--font-heading)', fontSize: '0.75rem', fontWeight: 600, color: 'var(--anthropic-sage)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Live & Operational</div>
                        <div style={{ fontSize: '1.8rem', fontWeight: 500, color: 'var(--anthropic-sage)' }}>{rawItems.filter(i => i.lifecycle_status === 'ACTIVE').length}</div>
                    </div>
                    {/* Exposed / Warning */}
                    <div onClick={() => setStatusFilter('EXPOSED')} style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', cursor: 'pointer', transition: 'transform 0.1s, border-color 0.2s' }} onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.borderColor = 'var(--text-muted)'; }} onMouseLeave={(e) => { e.currentTarget.style.transform = 'none'; e.currentTarget.style.borderColor = 'var(--border-color)'; }}>
                        <div style={{ fontFamily: 'var(--font-heading)', fontSize: '0.75rem', fontWeight: 600, color: 'var(--anthropic-terracotta)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>High Exposure</div>
                        <div style={{ fontSize: '1.8rem', fontWeight: 500, color: 'var(--anthropic-terracotta)' }}>{rawItems.filter(i => i.lifecycle_status === 'EXPOSED').length}</div>
                    </div>
                </div>

                {/* ─── FILTERS & SEARCH ─── */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '1.5rem' }}>
                    <div style={{ width: '400px' }}>
                        <Input
                            placeholder="Search by ID or Title..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            style={{ marginBottom: 0 }}
                        />
                    </div>
                    <div style={{ display: 'flex', gap: '0.75rem' }}>
                        <select
                            value={sectionFilter}
                            onChange={(e) => {
                                setSectionFilter(e.target.value);
                                setTypeFilter('All');
                            }}
                            style={selectStyle}
                        >
                            <option value="All">All Sections</option>
                            <option value="Reading">Reading</option>
                            <option value="Listening">Listening</option>
                            <option value="Speaking">Speaking</option>
                            <option value="Writing">Writing</option>
                        </select>

                        {sectionFilter !== 'All' && (
                            <select
                                value={typeFilter}
                                onChange={(e) => setTypeFilter(e.target.value)}
                                style={selectStyle}
                            >
                                <option value="All">All {sectionFilter} Types</option>
                                {sectionTaskTypes[sectionFilter]?.map(typeKey => (
                                    <option key={typeKey} value={typeKey}>
                                        {TASK_TYPE_LABELS[typeKey] || typeKey}
                                    </option>
                                ))}
                            </select>
                        )}
                        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} style={selectStyle}>
                            <option value="All">Status: All</option>
                            <option value="DRAFT">Draft</option>
                            <option value="REVIEW">Review</option>
                            <option value="FIELD_TEST">Field Test</option>
                            <option value="ACTIVE">Active</option>
                            <option value="SUSPENDED">Suspended</option>
                            <option value="EXPOSED">Exposed</option>
                            <option value="ARCHIVED">Archived</option>
                        </select>
                    </div>
                </div>

                <Card style={{ border: '1px solid var(--border-color)', boxShadow: 'none' }}>
                    <CardHeader style={{ padding: '1rem 1.5rem', borderBottom: '1px solid var(--border-color)', backgroundColor: 'var(--anthropic-cream)', borderRadius: '8px 8px 0 0' }}>
                        <div style={{ display: 'grid', gridTemplateColumns: '1.8fr 0.7fr 1.1fr 0.5fr 0.6fr 0.35fr 0.8fr 0.5fr 0.6fr 1fr', gap: '0.5rem', fontWeight: 600, fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', fontFamily: 'var(--font-heading)' }}>
                            <div>Content Title</div>
                            <div>Section</div>
                            <div>Item Type</div>
                            <div>Level</div>
                            <div>Diff (b)</div>
                            <div>Ver</div>
                            <div>Model</div>
                            <div>Age</div>
                            <div>Status</div>
                            <div style={{ textAlign: 'right' }}>Actions</div>
                        </div>
                    </CardHeader>
                    <CardContent style={{ padding: 0 }}>
                        {loading && <div style={{ padding: '1.5rem', textAlign: 'center' }}>Loading official 2026 Test Items...</div>}
                        {!loading && filteredItems.length === 0 && (
                            <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>
                                {rawItems.length === 0 ? 'No items found in the database.' : `No items match your filters.`}
                            </div>
                        )}
                        {!loading && filteredItems.map((item: any, index: number) => (
                            <TestItemRow
                                key={item.id}
                                item={item}
                                index={index}
                                totalCount={filteredItems.length}
                                openPreview={openPreview}
                                handleSingleQA={handleSingleQA}
                                router={router}
                                getStatusBadge={getStatusBadge}
                            />
                        ))}
                    </CardContent>
                </Card>
            </main>
        </div>
    );
}
