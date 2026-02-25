'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { API_BASE_URL } from '../lib/api-config';

// Components for all 12 task types
import { CompleteTheWords } from './CompleteTheWords';
import { ReadInDailyLife } from './ReadInDailyLife';
import { ReadAcademicPassage } from './ReadAcademicPassage';
import { ListenChooseResponse } from './ListenChooseResponse';
import { ListenConversation } from './ListenConversation';
import { ListenAnnouncement } from './ListenAnnouncement';
import { ListenAcademicTalk } from './ListenAcademicTalk';
import { BuildSentence } from './BuildSentence';
import { WriteEmail } from './WriteEmail';
import { WriteAcademicDiscussion } from './WriteAcademicDiscussion';
import { ListenRepeat } from './ListenRepeat';
import { InterviewUI } from './InterviewUI';

// Post-test components
import { ScoreReportDashboard } from './ScoreReportDashboard';
import { TestTimer } from './TestTimer';

/* ──────────────────────────────────────────────
   Test Assembly Configuration (demo-sized)
   Official counts: R=35, L=35, W=12, S=11
   Demo counts: enough to show all 12 types
   ────────────────────────────────────────────── */
const TEST_ASSEMBLY = [
    // READING
    { section: 'READING', task_type: 'COMPLETE_THE_WORDS', count: 2 },
    { section: 'READING', task_type: 'READ_IN_DAILY_LIFE', count: 2 },
    { section: 'READING', task_type: 'READ_ACADEMIC_PASSAGE', count: 1 },
    // LISTENING
    { section: 'LISTENING', task_type: 'LISTEN_CHOOSE_RESPONSE', count: 2 },
    { section: 'LISTENING', task_type: 'LISTEN_CONVERSATION', count: 1 },
    { section: 'LISTENING', task_type: 'LISTEN_ANNOUNCEMENT', count: 1 },
    { section: 'LISTENING', task_type: 'LISTEN_ACADEMIC_TALK', count: 1 },
    // WRITING (order per ETS: Build Sentence → Email → Discussion)
    { section: 'WRITING', task_type: 'BUILD_A_SENTENCE', count: 3 },
    { section: 'WRITING', task_type: 'WRITE_AN_EMAIL', count: 1 },
    { section: 'WRITING', task_type: 'WRITE_ACADEMIC_DISCUSSION', count: 1 },
    // SPEAKING (order per ETS: Listen & Repeat → Interview)
    { section: 'SPEAKING', task_type: 'LISTEN_AND_REPEAT', count: 2 },
    { section: 'SPEAKING', task_type: 'TAKE_AN_INTERVIEW', count: 1 },
];

const SECTION_ORDER = ['READING', 'LISTENING', 'WRITING', 'SPEAKING'] as const;

const SECTION_CONFIG: Record<string, { label: string; seconds: number }> = {
    READING: { label: 'Reading Section', seconds: 600 },  // 10 min demo
    LISTENING: { label: 'Listening Section', seconds: 600 },
    WRITING: { label: 'Writing Section', seconds: 600 },
    SPEAKING: { label: 'Speaking Section', seconds: 480 },  // 8 min
};

interface TestItem {
    id: string;
    section: string;
    task_type: string;
    prompt_content: string;
}

interface ParsedItem {
    id: string;
    section: string;
    task_type: string;
    content: any;
}

type Phase = 'LOADING' | 'SECTION_INTRO' | 'TEST' | 'SCORE';

/* ──────────────────────────────────────────────
   Fetch random items from backend
   ────────────────────────────────────────────── */
async function fetchTestItems(): Promise<ParsedItem[]> {
    const allItems: ParsedItem[] = [];
    const headers = { 'Bypass-Tunnel-Reminders': 'true' };

    for (const spec of TEST_ASSEMBLY) {
        try {
            const url = `${API_BASE_URL}/api/items/random?section=${spec.section}&task_type=${spec.task_type}&count=${spec.count}`;
            const res = await fetch(url, { headers });
            if (!res.ok) continue;
            const items: TestItem[] = await res.json();
            for (const item of items) {
                let content;
                try { content = JSON.parse(item.prompt_content); } catch { content = item.prompt_content; }
                allItems.push({ id: item.id, section: item.section, task_type: item.task_type, content });
            }
        } catch { /* skip failed fetches */ }
    }
    return allItems;
}

/* ──────────────────────────────────────────────
   Main TestSequencer Component
   ────────────────────────────────────────────── */
export const TestSequencer: React.FC = () => {
    const [phase, setPhase] = useState<Phase>('LOADING');
    const [items, setItems] = useState<ParsedItem[]>([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [currentSectionIdx, setCurrentSectionIdx] = useState(0);
    const [responses, setResponses] = useState<Record<string, any>>({});
    const [error, setError] = useState<string | null>(null);
    const [showConfirmDialog, setShowConfirmDialog] = useState(false);
    const [showReviewScreen, setShowReviewScreen] = useState(false);

    // Load items on mount
    useEffect(() => {
        fetchTestItems().then(fetched => {
            if (fetched.length === 0) {
                setError('No items found in the item bank. Please check the backend.');
                return;
            }
            setItems(fetched);
            setPhase('SECTION_INTRO');
        }).catch(() => setError('Failed to connect to the backend API.'));
    }, []);

    const currentItem = items[currentIndex];
    const currentSection = SECTION_ORDER[currentSectionIdx];

    // Get items for current section
    const sectionItems = items.filter(i => i.section === currentSection);
    const indexInSection = currentItem ? sectionItems.indexOf(currentItem) : 0;

    // Core advance logic (called after any confirmation)
    const advanceNext = useCallback(() => {
        const nextIndex = currentIndex + 1;
        if (nextIndex < items.length) {
            const nextItem = items[nextIndex];
            if (nextItem.section !== currentSection) {
                setCurrentSectionIdx(prev => prev + 1);
                setCurrentIndex(nextIndex);
                setPhase('SECTION_INTRO');
            } else {
                setCurrentIndex(nextIndex);
            }
        } else {
            setPhase('SCORE');
        }
    }, [currentIndex, items, currentSection]);

    // Section-aware Next handler
    const handleNext = useCallback(() => {
        if (currentSection === 'LISTENING') {
            // Listening: show confirmation dialog before advancing
            setShowConfirmDialog(true);
        } else {
            advanceNext();
        }
    }, [currentSection, advanceNext]);

    // Reading: go back within section
    const handleBack = useCallback(() => {
        if (currentSection !== 'READING') return;
        // Find the first item index of this section
        const sectionStart = items.findIndex(i => i.section === currentSection);
        if (currentIndex > sectionStart) {
            setCurrentIndex(currentIndex - 1);
        }
    }, [currentIndex, items, currentSection]);

    // Listening: confirm and advance
    const handleConfirmAdvance = useCallback(() => {
        setShowConfirmDialog(false);
        advanceNext();
    }, [advanceNext]);

    const saveResponse = useCallback((itemId: string, response: any) => {
        setResponses(prev => ({ ...prev, [itemId]: response }));
    }, []);

    // Check if Back is available (Reading only, not at first item of section)
    const isReading = currentSection === 'READING';
    const isListening = currentSection === 'LISTENING';
    const sectionStart = items.findIndex(i => i.section === currentSection);
    const canGoBack = isReading && currentIndex > sectionStart;

    /* ── LOADING ── */
    if (phase === 'LOADING' || error) {
        return (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', backgroundColor: '#f8f9fa' }}>
                <div style={{ textAlign: 'center' }}>
                    {error ? (
                        <>
                            <div style={{ fontSize: '48px', marginBottom: '16px' }}>⚠️</div>
                            <h2 style={{ color: '#dc3545' }}>Error</h2>
                            <p style={{ color: '#666' }}>{error}</p>
                        </>
                    ) : (
                        <>
                            <div style={{ fontSize: '48px', marginBottom: '16px' }}>⏳</div>
                            <h2 style={{ color: '#333' }}>Assembling Your Test...</h2>
                            <p style={{ color: '#666' }}>Fetching items from the item bank</p>
                        </>
                    )}
                </div>
            </div>
        );
    }

    /* ── SECTION INTRO ── */
    if (phase === 'SECTION_INTRO') {
        const cfg = SECTION_CONFIG[currentSection];
        const sectionCount = items.filter(i => i.section === currentSection).length;
        return (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', backgroundColor: '#1e293b' }}>
                <div style={{ textAlign: 'center', color: 'white', maxWidth: '500px' }}>
                    <div style={{ fontSize: '14px', textTransform: 'uppercase', letterSpacing: '3px', color: '#94a3b8', marginBottom: '12px' }}>
                        Section {currentSectionIdx + 1} of 4
                    </div>
                    <h1 style={{ fontSize: '36px', fontWeight: 700, margin: '0 0 16px' }}>{cfg.label}</h1>
                    <p style={{ color: '#cbd5e1', fontSize: '16px', marginBottom: '32px' }}>
                        {sectionCount} item{sectionCount !== 1 ? 's' : ''} • {Math.floor(cfg.seconds / 60)} minutes
                    </p>
                    <button
                        onClick={() => setPhase('TEST')}
                        style={{
                            padding: '12px 48px', fontSize: '16px', fontWeight: 600,
                            backgroundColor: '#3b82f6', color: 'white', border: 'none',
                            borderRadius: '8px', cursor: 'pointer'
                        }}
                    >
                        Begin Section
                    </button>
                </div>
            </div>
        );
    }

    /* ── SCORE REPORT ── */
    if (phase === 'SCORE') {
        const totalAnswered = Object.keys(responses).length;
        const band = 4.0; // Demo placeholder

        return (
            <ScoreReportDashboard
                candidateName="Test Candidate"
                etsId="DEMO"
                testDate={new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                scores={{
                    reading: { band, cefr: 'B2', legacyRange: '—' },
                    listening: { band, cefr: 'B2', legacyRange: '—' },
                    writing: { band, cefr: 'B2', legacyRange: '—' },
                    speaking: { band, cefr: 'B2', legacyRange: '—' },
                    total: { band, cefr: 'B2', legacyRange: '—' },
                }}
                myBest={{
                    reading: { band, date: 'Today' },
                    listening: { band, date: 'Today' },
                    speaking: { band, date: 'Today' },
                    writing: { band, date: 'Today' },
                    total: band,
                }}
                feedback={{
                    reading: `Completed ${totalAnswered} of ${items.length} items. Demo scoring — real AI scoring coming soon.`,
                    writing: 'Demo scoring — real AI scoring coming soon.'
                }}
            />
        );
    }

    /* ── TEST PHASE: Render current item ── */
    if (!currentItem) {
        setPhase('SCORE');
        return null;
    }

    const cfg = SECTION_CONFIG[currentSection];
    const c = currentItem.content;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
            {/* Header Bar */}
            <header style={{
                backgroundColor: '#1e293b', color: 'white',
                padding: '8px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                fontSize: '14px', flexShrink: 0
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <strong style={{ fontSize: '16px' }}>TOEFL iBT</strong>
                    <span style={{ padding: '2px 10px', backgroundColor: '#334155', borderRadius: '4px' }}>
                        {cfg.label}
                    </span>
                </div>
                <TestTimer
                    initialSeconds={cfg.seconds}
                    onTimeUp={handleNext}
                    sectionName=""
                />
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span style={{ color: '#94a3b8' }}>
                        Item {indexInSection + 1} of {sectionItems.length}
                    </span>
                    <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#22c55e' }} />
                </div>
            </header>

            {/* Content Area */}
            <main style={{ flex: 1, overflow: 'auto', position: 'relative' }}>
                {renderItem(currentItem, handleNext, saveResponse)}
            </main>

            {/* Footer Nav */}
            <footer style={{
                padding: '12px 24px', borderTop: '1px solid #e2e8f0',
                display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0,
                backgroundColor: '#f8fafc'
            }}>
                {/* Left: Back button (Reading only) */}
                <div>
                    {canGoBack && (
                        <button
                            onClick={handleBack}
                            style={{
                                padding: '8px 24px', fontSize: '14px', fontWeight: 600,
                                backgroundColor: '#FFFFFF', color: '#334155', border: '1px solid #cbd5e1',
                                borderRadius: '6px', cursor: 'pointer'
                            }}
                        >
                            ← Back
                        </button>
                    )}
                </div>

                {/* Center: Review button (Reading only) */}
                <div>
                    {isReading && (
                        <button
                            onClick={() => setShowReviewScreen(true)}
                            style={{
                                padding: '8px 24px', fontSize: '14px', fontWeight: 600,
                                backgroundColor: '#FFFFFF', color: '#334155', border: '1px solid #cbd5e1',
                                borderRadius: '6px', cursor: 'pointer'
                            }}
                        >
                            Review
                        </button>
                    )}
                </div>

                {/* Right: Next / Finish */}
                <div>
                    <button
                        onClick={handleNext}
                        style={{
                            padding: '8px 32px', fontSize: '14px', fontWeight: 600,
                            backgroundColor: '#3b82f6', color: 'white', border: 'none',
                            borderRadius: '6px', cursor: 'pointer'
                        }}
                    >
                        {currentIndex === items.length - 1 ? 'Finish Test' : 'Next →'}
                    </button>
                </div>
            </footer>

            {/* ── Listening Confirm Dialog ── */}
            {showConfirmDialog && (
                <div style={{
                    position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.6)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
                }}>
                    <div style={{
                        backgroundColor: '#FFFFFF', borderRadius: '12px', padding: '32px 40px',
                        maxWidth: '420px', width: '90%', textAlign: 'center',
                        boxShadow: '0 20px 60px rgba(0,0,0,0.3)'
                    }}>
                        <div style={{ fontSize: '32px', marginBottom: '16px' }}>⚠️</div>
                        <h3 style={{ margin: '0 0 12px', fontSize: '18px', color: '#1e293b' }}>
                            Confirm Your Answer
                        </h3>
                        <p style={{ color: '#64748b', fontSize: '14px', lineHeight: 1.6, marginBottom: '24px' }}>
                            Once confirmed, you <strong>cannot go back</strong> to this question.
                            Are you sure you want to proceed?
                        </p>
                        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
                            <button
                                onClick={() => setShowConfirmDialog(false)}
                                style={{
                                    padding: '10px 28px', fontSize: '14px', fontWeight: 600,
                                    backgroundColor: '#FFFFFF', color: '#334155', border: '1px solid #cbd5e1',
                                    borderRadius: '6px', cursor: 'pointer'
                                }}
                            >
                                Go Back
                            </button>
                            <button
                                onClick={handleConfirmAdvance}
                                style={{
                                    padding: '10px 28px', fontSize: '14px', fontWeight: 600,
                                    backgroundColor: '#dc2626', color: 'white', border: 'none',
                                    borderRadius: '6px', cursor: 'pointer'
                                }}
                            >
                                Confirm Answer
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* ── Reading Review Screen ── */}
            {showReviewScreen && (
                <div style={{
                    position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.6)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
                }}>
                    <div style={{
                        backgroundColor: '#FFFFFF', borderRadius: '12px', padding: '32px',
                        maxWidth: '520px', width: '90%',
                        boxShadow: '0 20px 60px rgba(0,0,0,0.3)', maxHeight: '80vh', overflow: 'auto'
                    }}>
                        <h3 style={{ margin: '0 0 8px', fontSize: '20px', color: '#1e293b' }}>Review — {cfg.label}</h3>
                        <p style={{ color: '#64748b', fontSize: '14px', marginBottom: '20px' }}>
                            Click any item to jump to it. You may change your answers.
                        </p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            {sectionItems.map((item, idx) => {
                                const answered = !!responses[item.id];
                                const isCurrent = items.indexOf(item) === currentIndex;
                                return (
                                    <button
                                        key={item.id}
                                        onClick={() => {
                                            setCurrentIndex(items.indexOf(item));
                                            setShowReviewScreen(false);
                                        }}
                                        style={{
                                            display: 'flex', alignItems: 'center', gap: '12px',
                                            padding: '12px 16px', fontSize: '14px',
                                            backgroundColor: isCurrent ? '#eff6ff' : '#FFFFFF',
                                            border: isCurrent ? '2px solid #3b82f6' : '1px solid #e2e8f0',
                                            borderRadius: '8px', cursor: 'pointer', textAlign: 'left', width: '100%'
                                        }}
                                    >
                                        <span style={{
                                            width: '24px', height: '24px', borderRadius: '50%',
                                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                                            fontSize: '12px', fontWeight: 700, flexShrink: 0,
                                            backgroundColor: answered ? '#22c55e' : '#e2e8f0',
                                            color: answered ? '#FFFFFF' : '#94a3b8'
                                        }}>
                                            {answered ? '✓' : idx + 1}
                                        </span>
                                        <span style={{ color: '#334155' }}>
                                            Item {idx + 1} — {item.task_type.replace(/_/g, ' ')}
                                        </span>
                                        {!answered && (
                                            <span style={{ marginLeft: 'auto', fontSize: '12px', color: '#f59e0b', fontWeight: 600 }}>Unanswered</span>
                                        )}
                                    </button>
                                );
                            })}
                        </div>
                        <div style={{ marginTop: '20px', textAlign: 'center' }}>
                            <button
                                onClick={() => setShowReviewScreen(false)}
                                style={{
                                    padding: '10px 32px', fontSize: '14px', fontWeight: 600,
                                    backgroundColor: '#3b82f6', color: 'white', border: 'none',
                                    borderRadius: '6px', cursor: 'pointer'
                                }}
                            >
                                Return to Test
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

/* ──────────────────────────────────────────────
   Item Renderer — maps task_type → component
   ────────────────────────────────────────────── */
function renderItem(
    item: ParsedItem,
    onNext: () => void,
    saveResponse: (id: string, data: any) => void
): React.ReactNode {
    const c = item.content;

    switch (item.task_type) {

        /* ── READING ── */

        case 'COMPLETE_THE_WORDS': {
            // Transform DB text (ro___) → HTML with <input class="ets-inline-cloze">
            const rawText = c.text || c.stimulus || '';
            const questions = c.questions || [];
            // Build a lookup from gap text → correct answer
            const gapMap: Record<string, string> = {};
            questions.forEach((q: any) => {
                if (q.text && q.correct_answer) gapMap[q.text] = q.correct_answer;
            });
            // Convert underscores to interactive inputs
            let wordIdx = 0;
            const stimulusHTML = rawText.replace(/(\S*?)(_{2,})(\S*)/g, (_match: string, prefix: string, underscores: string, suffix: string) => {
                const id = `w${wordIdx++}`;
                const missingLen = underscores.length;
                return `${prefix}<input class="ets-inline-cloze" data-word-id="${id}" maxlength="${missingLen}" style="width:${missingLen * 12 + 8}px; border:none; border-bottom:2px solid #005587; font-size:16px; font-family:inherit; text-align:center; background:transparent; outline:none;" />${suffix}`;
            });
            return (
                <CompleteTheWords
                    stimulusHTML={stimulusHTML}
                    onWordComplete={(wordId, val) => saveResponse(item.id, { [wordId]: val })}
                />
            );
        }

        case 'READ_IN_DAILY_LIFE': {
            const questions = c.questions || [];
            const passageText = c.text || '';
            // Daily Life items have text content, not images — render inline
            return (
                <div style={{ display: 'flex', height: '100%', fontFamily: "'Times New Roman', Times, serif" }}>
                    {/* Left: Passage */}
                    <div style={{ flex: '1 1 50%', padding: '24px', overflowY: 'auto', borderRight: '2px solid #005587' }}>
                        <h3 style={{ color: '#005587', marginBottom: '12px' }}>{c.title || 'Read in Daily Life'}</h3>
                        <div style={{ fontSize: '16px', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>{passageText}</div>
                    </div>
                    {/* Right: Questions */}
                    <div style={{ flex: '1 1 50%', padding: '24px', overflowY: 'auto' }}>
                        {questions.map((q: any, qi: number) => (
                            <div key={qi} style={{ marginBottom: '24px' }}>
                                <p style={{ fontWeight: 600, marginBottom: '8px' }}>{q.question_num || qi + 1}. {q.text}</p>
                                {(q.options || []).map((opt: string, oi: number) => (
                                    <label key={oi} style={{ display: 'block', padding: '6px 0', cursor: 'pointer' }}>
                                        <input
                                            type="radio"
                                            name={`q-${item.id}-${qi}`}
                                            onChange={() => saveResponse(item.id, { question: qi, answer: oi })}
                                            style={{ marginRight: '8px' }}
                                        />
                                        {opt}
                                    </label>
                                ))}
                            </div>
                        ))}
                    </div>
                </div>
            );
        }

        case 'READ_ACADEMIC_PASSAGE': {
            const questions = c.questions || [];
            return (
                <ReadAcademicPassage
                    title={c.title || 'Academic Passage'}
                    content={c.text || ''}
                >
                    <div style={{ padding: '20px' }}>
                        {questions.map((q: any, qi: number) => (
                            <div key={qi} style={{ marginBottom: '24px' }}>
                                <p style={{ fontWeight: 600, marginBottom: '8px' }}>{q.question_num || qi + 1}. {q.text}</p>
                                {(q.options || []).map((opt: string, oi: number) => (
                                    <label key={oi} style={{ display: 'block', padding: '6px 0', cursor: 'pointer' }}>
                                        <input
                                            type="radio"
                                            name={`q-${item.id}-${qi}`}
                                            onChange={() => saveResponse(item.id, { question: qi, answer: oi })}
                                            style={{ marginRight: '8px' }}
                                        />
                                        {opt}
                                    </label>
                                ))}
                            </div>
                        ))}
                    </div>
                </ReadAcademicPassage>
            );
        }

        /* ── LISTENING ── */
        // Using refined components. Audio served from frontend public/ at /audio/...
        // No transcripts shown — it's a listening test.

        case 'LISTEN_CHOOSE_RESPONSE': {
            const q = (c.questions || [{}])[0];
            return (
                <ListenChooseResponse
                    audioUrl={c.audio_url ? `/${c.audio_url}` : ''}
                    options={q.options || []}
                    onOptionSelect={(idx) => saveResponse(item.id, { answer: idx })}
                />
            );
        }

        case 'LISTEN_CONVERSATION': {
            const q = (c.questions || [{}])[0];
            return (
                <ListenConversation
                    audioUrl={c.audio_url ? `/${c.audio_url}` : ''}
                    questionText={q.question || q.text || 'What is the conversation mainly about?'}
                    options={q.options || []}
                    onOptionSelect={(idx) => saveResponse(item.id, { answer: idx })}
                />
            );
        }

        case 'LISTEN_ANNOUNCEMENT': {
            const q = (c.questions || [{}])[0];
            return (
                <ListenAnnouncement
                    audioUrl={c.audio_url ? `/${c.audio_url}` : ''}
                    questionText={q.question || q.text || 'What is the announcement mainly about?'}
                    options={q.options || []}
                    onOptionSelect={(idx) => saveResponse(item.id, { answer: idx })}
                />
            );
        }

        case 'LISTEN_ACADEMIC_TALK': {
            const q = (c.questions || [{}])[0];
            return (
                <ListenAcademicTalk
                    audioUrl={c.audio_url ? `/${c.audio_url}` : ''}
                    questionText={q.question || q.text || 'What is the talk mainly about?'}
                    options={q.options || []}
                    onOptionSelect={(idx) => saveResponse(item.id, { answer: idx })}
                />
            );
        }

        /* ── WRITING ── */

        case 'BUILD_A_SENTENCE': {
            return (
                <div style={{ padding: '24px', maxWidth: '800px', margin: '0 auto' }}>
                    <BuildSentence
                        contextSpeakerUrl="/images/avatars/professor.jpg"
                        contextText={c.context || ''}
                        builderSpeakerUrl="/images/avatars/male_student_andrew.jpg"
                        prefixText=""
                        suffixText={c.endPunctuation || '.'}
                        scrambledWords={c.fragments || []}
                        onSentenceUpdate={(order) => saveResponse(item.id, { order })}
                    />
                </div>
            );
        }

        case 'WRITE_AN_EMAIL': {
            const promptHTML = `
        <div style="font-family: 'Times New Roman', Times, serif; font-size: 16px; line-height: 1.4;">
          <p>${c.scenario || ''}</p>
          <p><strong>In your email, you should:</strong></p>
          <ul style="padding-left: 20px;">
            ${(c.bullets || []).map((b: string) => `<li style="margin-bottom: 5px; list-style-type: disc;">${b}</li>`).join('')}
          </ul>
          <p>Write as much as you can and in complete sentences.</p>
        </div>
      `;
            return (
                <WriteEmail
                    promptHTML={promptHTML}
                    emailTo={c.emailTo || 'recipient@university.edu'}
                    emailSubject={c.topic || 'Your Message'}
                    onSave={(text) => saveResponse(item.id, { text })}
                />
            );
        }

        case 'WRITE_ACADEMIC_DISCUSSION': {
            return (
                <WriteAcademicDiscussion
                    professorName="Professor"
                    professorAvatarUrl="/images/avatars/professor.jpg"
                    professorPromptHTML={c.professor_prompt || ''}
                    studentPosts={[
                        {
                            id: 's1',
                            authorName: c.student_1_name || 'Student A',
                            avatarUrl: '/images/avatars/male_student_andrew.jpg',
                            text: c.student_1_response || '',
                        },
                        {
                            id: 's2',
                            authorName: c.student_2_name || 'Student B',
                            avatarUrl: '/images/avatars/female_student_kelly.jpg',
                            text: c.student_2_response || '',
                        },
                    ]}
                    onSave={(text) => saveResponse(item.id, { text })}
                />
            );
        }

        /* ── SPEAKING ── */

        case 'LISTEN_AND_REPEAT': {
            const sentences = c.sentences || [];
            const firstSentence = sentences[0];
            return (
                <ListenRepeat
                    imageUrl={firstSentence?.image_url || '/images/listen_repeat_zoo_sample.jpg'}
                    imageAlt={c.title || 'Listen and repeat'}
                />
            );
        }

        case 'TAKE_AN_INTERVIEW': {
            return (
                <InterviewUI
                    promptVideoUrl="/legacy_idle_loop.mp4"
                    maxRecordTimeSeconds={45}
                    websocketUrl="ws://localhost:8000/ws/audio"
                />
            );
        }

        default:
            return (
                <div style={{ padding: '40px', textAlign: 'center', color: '#666' }}>
                    <p>Unknown task type: <strong>{item.task_type}</strong></p>
                    <p>Item ID: {item.id}</p>
                </div>
            );
    }
}
