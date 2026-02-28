'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { API_BASE_URL } from '../lib/api-config';

import { CompleteTheWords } from './CompleteTheWords';
import { ClozeParagraph } from './ClozeParagraph';
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
import { ScoreReportDashboard } from './ScoreReportDashboard';
import { TestTimer } from './TestTimer';
import { useTestStore } from '../store/testStore';
import { useRouter } from 'next/navigation';

/* ══════════════════════════════════════════════════════════════════════════
   MST TEST ASSEMBLY — ETS TOEFL iBT 2026 Spec
   ══════════════════════════════════════════════════════════════════════════ */

// Slot = a batch request: "fetch N items of this type with this prefix"
interface Slot { section: string; task_type: string; count: number; prefix: string; }

// MST modules per section
const READING_ROUTER: Slot[] = [
    { section: 'READING', task_type: 'COMPLETE_THE_WORDS', count: 10, prefix: 'B' },
    { section: 'READING', task_type: 'READ_IN_DAILY_LIFE', count: 5, prefix: 'D' },
    { section: 'READING', task_type: 'READ_ACADEMIC_PASSAGE', count: 5, prefix: 'E' },
];
const READING_LOWER: Slot[] = [
    { section: 'READING', task_type: 'COMPLETE_THE_WORDS', count: 10, prefix: 'A' },
    { section: 'READING', task_type: 'READ_IN_DAILY_LIFE', count: 5, prefix: 'D' },
];
const READING_UPPER: Slot[] = [
    { section: 'READING', task_type: 'COMPLETE_THE_WORDS', count: 10, prefix: 'C' },
    { section: 'READING', task_type: 'READ_ACADEMIC_PASSAGE', count: 5, prefix: 'E' },
];

const LISTENING_ROUTER: Slot[] = [
    { section: 'LISTENING', task_type: 'LISTEN_CHOOSE_RESPONSE', count: 8, prefix: 'R' },
    { section: 'LISTENING', task_type: 'LISTEN_CONVERSATION', count: 4, prefix: '' },
    { section: 'LISTENING', task_type: 'LISTEN_ANNOUNCEMENT', count: 4, prefix: '' },
    { section: 'LISTENING', task_type: 'LISTEN_ACADEMIC_TALK', count: 4, prefix: '' },
];
const LISTENING_LOWER: Slot[] = [
    { section: 'LISTENING', task_type: 'LISTEN_CHOOSE_RESPONSE', count: 7, prefix: 'R' },
    { section: 'LISTENING', task_type: 'LISTEN_CONVERSATION', count: 4, prefix: '' },
    { section: 'LISTENING', task_type: 'LISTEN_ANNOUNCEMENT', count: 4, prefix: '' },
];
const LISTENING_UPPER: Slot[] = [
    { section: 'LISTENING', task_type: 'LISTEN_CHOOSE_RESPONSE', count: 3, prefix: 'R' },
    { section: 'LISTENING', task_type: 'LISTEN_CONVERSATION', count: 4, prefix: 'E' },
    { section: 'LISTENING', task_type: 'LISTEN_ACADEMIC_TALK', count: 8, prefix: '' },
];

const WRITING_LINEAR: Slot[] = [
    { section: 'WRITING', task_type: 'BUILD_A_SENTENCE', count: 10, prefix: '' },
    { section: 'WRITING', task_type: 'WRITE_AN_EMAIL', count: 1, prefix: 'E' },
    { section: 'WRITING', task_type: 'WRITE_ACADEMIC_DISCUSSION', count: 1, prefix: 'E' },
];

const SPEAKING_LINEAR: Slot[] = [
    { section: 'SPEAKING', task_type: 'LISTEN_AND_REPEAT', count: 7, prefix: '' },
    { section: 'SPEAKING', task_type: 'TAKE_AN_INTERVIEW', count: 4, prefix: '' },
];

const SECTION_ORDER = ['READING', 'LISTENING', 'WRITING', 'SPEAKING'] as const;
type SectionName = typeof SECTION_ORDER[number];

const THEME = {
    teal: '#006A70', tealDark: '#004d52', tealLight: '#e6f2f3',
    navy: '#1e293b', accent: '#f59e0b', success: '#10b981',
    bg: '#f8fafc', white: '#ffffff', text: '#334155'
};

const SEC = {
    READING: { label: 'Reading', icon: '📖', time: 1800, desc: 'Analyze passages and complete texts.' },
    LISTENING: { label: 'Listening', icon: '🎧', time: 1800, desc: 'Respond to academic talks and conversations.' },
    WRITING: { label: 'Writing', icon: '✍️', time: 900, desc: 'Compose emails and academic responses.' },
    SPEAKING: { label: 'Speaking', icon: '🎙️', time: 480, desc: 'Respond to prompts and interviews.' },
};

const MST_THRESHOLD = 0.6; // 60 % correct → upper module

interface ParsedItem {
    id: string; section: string; task_type: string; content: any;
    questions?: any[];
    stage: 'router' | 'lower' | 'upper' | 'linear';
}

type Phase = 'LOADING' | 'INTRO' | 'TEST' | 'MST_ROUTING' | 'FINISHED';

/* ── helpers ───────────────────────────────────────────────────────────── */

const HEADERS = { 'Bypass-Tunnel-Reminder': 'true' };

async function fetchSlots(slots: Slot[], stage: ParsedItem['stage'], exclude: Set<string>): Promise<ParsedItem[]> {
    const out: ParsedItem[] = [];
    for (const s of slots) {
        const url = `${API_BASE_URL}/api/items/filter?source_id_prefix=${s.prefix}&section=${s.section}`;
        const res = await fetch(url, { headers: HEADERS });
        if (!res.ok) continue;
        const data: any[] = await res.json();
        const matches = data
            .filter((i: any) => i.task_type === s.task_type && !exclude.has(i.id))
            .slice(0, s.count);
        for (const item of matches) {
            let content: any;
            try { content = JSON.parse(item.prompt_content); } catch { content = item.prompt_content; }

            if ((item.task_type === 'READ_IN_DAILY_LIFE' || item.task_type === 'READ_ACADEMIC_PASSAGE') && item.questions && item.questions.length > 0) {
                item.questions.forEach((db_q: any, qi: number) => {
                    const originalQ = content.questions?.[qi] || db_q;
                    const singleQContent = { ...content, questions: [originalQ] };
                    out.push({
                        id: `${item.id}-${qi}`,
                        section: item.section,
                        task_type: item.task_type,
                        content: singleQContent,
                        questions: [db_q],
                        stage
                    });
                });
            } else {
                out.push({ id: item.id, section: item.section, task_type: item.task_type, content, questions: item.questions || [], stage });
            }
            exclude.add(item.id);
        }
    }
    return out;
}

function scoreItems(items: ParsedItem[], responses: Record<string, any>): { correct: number; total: number } {
    let correct = 0;
    let total = 0;

    for (const item of items) {
        const questions = item.content?.questions || [];
        const rawResp = responses[item.id];

        if (item.task_type === 'COMPLETE_THE_WORDS') {
            const qsToScore = item.questions?.length ? item.questions : questions;
            const numGaps = qsToScore.length || 10;
            total += numGaps;

            const raw = item.content?.text || item.content?.stimulus || '';
            const blanks: { p: string, s: string }[] = [];
            raw.replace(/(\S*?)(_+)(\S*)/g, (_m: string, p: string, u: string, s: string) => {
                blanks.push({ p, s });
                return _m;
            });

            for (let i = 0; i < qsToScore.length; i++) {
                const q = qsToScore[i];
                const expected = q.correct_answer;

                let userAns: any;
                if (q.id && responses[q.id] !== undefined) {
                    userAns = responses[q.id];
                } else if (rawResp) {
                    try {
                        const parsed = typeof rawResp === 'string' ? JSON.parse(rawResp) : rawResp;
                        userAns = parsed[`w${i}`];
                    } catch { }
                }

                if (userAns !== undefined && userAns !== null) {
                    const uAnsStr = String(userAns).trim().toLowerCase();
                    const expStr = String(expected).trim().toLowerCase();
                    const b = blanks[i] || { p: '', s: '' };
                    const combined = (b.p + uAnsStr + b.s).toLowerCase();

                    if (uAnsStr === expStr || combined === expStr || combined.replace(/[^a-z]/g, '') === expStr.replace(/[^a-z]/g, '')) {
                        correct++;
                    }
                }
            }
        } else if (item.task_type === 'BUILD_A_SENTENCE') {
            total++;
            const expected = item.content?.fragments || [];
            let userOrder: any[] = [];

            const qid = item.questions?.[0]?.id;
            if (qid && responses[qid]) {
                try { userOrder = JSON.parse(responses[qid]); } catch { }
            } else if (rawResp) {
                try {
                    const parsed = typeof rawResp === 'string' ? JSON.parse(rawResp) : rawResp;
                    userOrder = parsed.order || [];
                } catch { }
            }

            if (expected.length > 0 && userOrder.length > 0 && userOrder.join(' ').toLowerCase() === expected.join(' ').toLowerCase()) {
                correct++;
            }
        } else {
            const qsToScore = item.questions?.length ? item.questions : questions;
            if (qsToScore.length === 0) {
                total++;
                continue;
            }

            for (let i = 0; i < qsToScore.length; i++) {
                const q = qsToScore[i];
                const key = q.correct_answer;
                if (key === undefined || key === null) continue;
                total++;

                let userAns: any;
                if (q.id && responses[q.id] !== undefined) {
                    userAns = responses[q.id];
                } else if (rawResp) {
                    try {
                        const parsed = typeof rawResp === 'string' ? JSON.parse(rawResp) : rawResp;
                        userAns = parsed[`q${i}_answer`] ?? parsed.answer;
                    } catch {
                        userAns = rawResp;
                    }
                }

                if (userAns !== undefined && Number(userAns) === Number(key)) {
                    correct++;
                }
            }
        }
    }
    return { correct, total };
}

/* ══════════════════════════════════════════════════════════════════════════
   COMPONENT
   ══════════════════════════════════════════════════════════════════════════ */
export const TestSequencer: React.FC = () => {
    const [phase, setPhase] = useState<Phase>('LOADING');
    const [items, setItems] = useState<ParsedItem[]>([]);
    const [idx, setIdx] = useState(0);
    const [secIdx, setSecIdx] = useState(0);
    const router = useRouter();
    const setAnswer = useTestStore(s => s.setAnswer);
    const answers = useTestStore(s => s.answers);
    const isSubmitting = useTestStore(s => s.isSubmitting);
    const submitTest = useTestStore(s => s.submitTest);
    const sessionId = useTestStore(s => s.sessionId);
    const [error, setError] = useState<string | null>(null);
    const [confirming, setConfirming] = useState(false);
    const [reviewing, setReviewing] = useState(false);
    const [routeInfo, setRouteInfo] = useState<{ score: number; total: number; path: string } | null>(null);
    const usedIds = useRef<Set<string>>(new Set());

    // ── INIT: fetch Router modules + linear sections & Register Session ──
    useEffect(() => {
        (async () => {
            try {
                // Register session in DB
                const studentId = localStorage.getItem('user_id') || 'demo_student_id';
                const sessionRes = await fetch(`${API_BASE_URL}/api/sessions`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Bypass-Tunnel-Reminder': 'true'
                    },
                    body: JSON.stringify({ student_id: studentId })
                });
                if (sessionRes.ok) {
                    const sessionData = await sessionRes.json();
                    useTestStore.getState().setSessionId(sessionData.id);
                }

                // Load test items
                const pool: ParsedItem[] = [];
                pool.push(...await fetchSlots(READING_ROUTER, 'router', usedIds.current));
                pool.push(...await fetchSlots(LISTENING_ROUTER, 'router', usedIds.current));
                pool.push(...await fetchSlots(WRITING_LINEAR, 'linear', usedIds.current));
                pool.push(...await fetchSlots(SPEAKING_LINEAR, 'linear', usedIds.current));
                if (pool.length === 0) { setError('Item bank empty.'); return; }
                setItems(pool);
                setPhase('INTRO');
            } catch { setError('Backend connection failed.'); }
        })();
    }, []);

    const cur = items[idx];
    const sec = SECTION_ORDER[secIdx];
    const secItems = items.filter(i => i.section === sec);
    const idxInSec = cur ? secItems.indexOf(cur) : 0;

    // ── MST ROUTING: inject Stage 2 items ──
    const performMstRouting = useCallback(async () => {
        const routerItems = items.filter(i => i.section === sec && i.stage === 'router');
        const { correct, total } = scoreItems(routerItems, answers);
        const ratio = total > 0 ? correct / total : 0;
        const goUpper = ratio >= MST_THRESHOLD;
        const path = goUpper ? 'UPPER' : 'LOWER';

        setRouteInfo({ score: correct, total, path });
        setPhase('MST_ROUTING');

        // Fetch the right Stage 2 module
        const stage2Slots = sec === 'READING'
            ? (goUpper ? READING_UPPER : READING_LOWER)
            : (goUpper ? LISTENING_UPPER : LISTENING_LOWER);

        const stage2Items = await fetchSlots(stage2Slots, goUpper ? 'upper' : 'lower', usedIds.current);

        // Splice Stage 2 items right after the current Router items
        setItems(prev => {
            const insertAfter = prev.findIndex((p, i) => p.section === sec && i >= idx) === -1
                ? idx + 1 : idx + 1;
            const copy = [...prev];
            copy.splice(insertAfter, 0, ...stage2Items);
            return copy;
        });

        // Brief routing animation, then continue
        setTimeout(() => {
            setIdx(prev => prev + 1);
            setRouteInfo(null);
            setPhase('TEST');
        }, 2200);
    }, [items, idx, sec, answers]);

    // ── ADVANCE logic ──
    const advance = useCallback(() => {
        const next = idx + 1;
        const curItem = items[idx];

        // Check if this is the last Router item before a section boundary
        const isMstSection = sec === 'READING' || sec === 'LISTENING';
        const isLastRouterInSection = isMstSection && curItem.stage === 'router' &&
            (next >= items.length || items[next].section !== sec || items[next].stage !== 'router');

        if (isLastRouterInSection) {
            // Check if Stage 2 already injected
            const hasStage2 = items.some(i => i.section === sec && (i.stage === 'upper' || i.stage === 'lower'));
            if (!hasStage2) {
                performMstRouting();
                return;
            }
        }

        // Normal advance
        if (next < items.length) {
            if (items[next].section !== sec) {
                setSecIdx(prev => prev + 1);
                setIdx(next);
                setPhase('INTRO');
            } else {
                setIdx(next);
            }
        } else {
            setPhase('FINISHED');
        }
    }, [idx, items, sec, performMstRouting]);

    const handleNext = () => {
        if (sec === 'LISTENING') setConfirming(true);
        else advance();
    };

    const save = (data: any) => {
        if (!cur) return;
        let currentObj = {};
        const currentStr = answers[cur.id];
        if (currentStr) {
            try { currentObj = JSON.parse(currentStr); } catch { /* ignore */ }
        }
        setAnswer(cur.id, JSON.stringify({ ...currentObj, ...data }));
    };

    /* ── RENDER PHASES ──────────────────────────────────────────────────── */

    // LOADING
    if (phase === 'LOADING') {
        return (
            <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: THEME.navy }}>
                <div style={{ textAlign: 'center' }}>
                    <div style={{ width: 60, height: 60, border: `4px solid ${THEME.teal}44`, borderTopColor: THEME.teal, borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 24px' }} />
                    <h2 style={{ color: 'white', fontWeight: 300, letterSpacing: 2 }}>ASSEMBLING TEST…</h2>
                    {error && <p style={{ color: '#f87171', marginTop: 16 }}>{error}</p>}
                </div>
                <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
            </div>
        );
    }

    // SECTION INTRO
    if (phase === 'INTRO') {
        const s = SEC[sec];
        return (
            <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: `linear-gradient(135deg, ${THEME.teal}, ${THEME.tealDark})`, color: 'white' }}>
                <div style={{ maxWidth: 600, textAlign: 'center', animation: 'fadeUp .7s ease' }}>
                    <div style={{ fontSize: 80, marginBottom: 20 }}>{s.icon}</div>
                    <h4 style={{ textTransform: 'uppercase', letterSpacing: 4, opacity: .7, marginBottom: 8 }}>Section {secIdx + 1} of 4</h4>
                    <h1 style={{ fontSize: 52, fontWeight: 700, marginBottom: 16 }}>{s.label}</h1>
                    <p style={{ fontSize: 18, opacity: .85, lineHeight: 1.6, marginBottom: 36 }}>{s.desc}</p>
                    <div style={{ display: 'flex', gap: 20, justifyContent: 'center', marginBottom: 40 }}>
                        <StatBox label="QUESTIONS" value={secItems.length} />
                        <StatBox label="TIME LIMIT" value={`${Math.floor(s.time / 60)}m`} />
                        {(sec === 'READING' || sec === 'LISTENING') && <StatBox label="ADAPTIVE" value="MST" />}
                    </div>
                    <button onClick={async () => {
                        if (sec === 'SPEAKING') {
                            try {
                                await navigator.mediaDevices.getUserMedia({ audio: true });
                            } catch (e) {
                                console.error("Mic access denied or error", e);
                            }
                        }
                        setPhase('TEST');
                    }}
                        style={{ padding: '18px 64px', fontSize: 18, fontWeight: 700, borderRadius: 50, border: 'none', background: 'white', color: THEME.teal, cursor: 'pointer', boxShadow: '0 10px 30px rgba(0,0,0,.25)', transition: 'transform .15s' }}
                        onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.05)'}
                        onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
                    >BEGIN SECTION</button>
                </div>
                <style>{`@keyframes fadeUp{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:translateY(0)}}`}</style>
            </div>
        );
    }

    // MST ROUTING ANIMATION
    if (phase === 'MST_ROUTING' && routeInfo) {
        return (
            <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: THEME.navy, color: 'white' }}>
                <div style={{ textAlign: 'center', animation: 'fadeUp .6s ease' }}>
                    <div style={{ fontSize: 56, marginBottom: 20 }}>🧠</div>
                    <h2 style={{ fontSize: 28, fontWeight: 300, marginBottom: 12 }}>Adaptive Routing</h2>
                    <p style={{ fontSize: 16, opacity: .7, marginBottom: 32 }}>Analyzing Stage 1 performance…</p>
                    <div style={{ display: 'flex', gap: 20, justifyContent: 'center', marginBottom: 32 }}>
                        <StatBox label="CORRECT" value={routeInfo.score} />
                        <StatBox label="TOTAL" value={routeInfo.total} />
                        <StatBox label="MODULE" value={routeInfo.path} highlight />
                    </div>
                    <div style={{ width: 200, height: 6, background: '#ffffff22', borderRadius: 10, margin: '0 auto', overflow: 'hidden' }}>
                        <div style={{ height: '100%', background: THEME.teal, animation: 'grow 2s ease forwards' }} />
                    </div>
                </div>
                <style>{`
          @keyframes fadeUp{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:translateY(0)}}
          @keyframes grow{from{width:0}to{width:100%}}
        `}</style>
            </div>
        );
    }

    // FINISHED
    if (phase === 'FINISHED') {
        const handleSubmit = async () => {
            await submitTest();
            router.push('/results');
        };

        return (
            <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: THEME.bg }}>
                <div style={{ textAlign: 'center', background: 'white', padding: 60, borderRadius: 24, boxShadow: '0 20px 40px rgba(0,0,0,0.05)', maxWidth: 500, width: '90%' }}>
                    {isSubmitting ? (
                        <>
                            <div style={{ width: 60, height: 60, border: `4px solid ${THEME.teal}44`, borderTopColor: THEME.teal, borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 24px' }} />
                            <h2 style={{ fontSize: 24, fontWeight: 700, color: THEME.navy, marginBottom: 8 }}>Submitting Test...</h2>
                            <p style={{ color: '#64748b' }}>AI is analyzing your responses.</p>
                        </>
                    ) : (
                        <>
                            <div style={{ fontSize: 64, marginBottom: 24 }}>🎓</div>
                            <h2 style={{ fontSize: 32, fontWeight: 800, color: THEME.navy, marginBottom: 12 }}>You've finished!</h2>
                            <p style={{ color: '#64748b', fontSize: 16, marginBottom: 36 }}>Click below to submit your securely encrypted responses for AI scoring.</p>
                            <button onClick={handleSubmit}
                                style={{ padding: '16px 48px', fontSize: 18, fontWeight: 700, borderRadius: 12, border: 'none', background: THEME.teal, color: 'white', cursor: 'pointer', boxShadow: `0 4px 14px ${THEME.teal}66`, transition: 'transform .15s' }}
                                onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-2px)'}
                                onMouseLeave={e => e.currentTarget.style.transform = 'translateY(0)'}
                            >Submit & View Results</button>
                        </>
                    )}
                </div>
                <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
            </div>
        );
    }

    // TEST PHASE
    if (!cur) { setPhase('FINISHED'); return null; }
    const s = SEC[sec];
    const isReading = sec === 'READING';

    return (
        <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', background: THEME.bg }}>
            {/* HEADER */}
            <header style={{ display: 'flex', flexDirection: 'column', flexShrink: 0 }}>
                <div style={{ background: THEME.navy, color: 'white', padding: '12px 30px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: `4px solid ${THEME.teal}` }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                        <span style={{ fontWeight: 800, fontSize: 20 }}>TOEFL<span style={{ color: THEME.teal }}>iBT</span></span>
                        <span style={{ background: THEME.teal, padding: '4px 14px', borderRadius: 4, fontSize: 11, fontWeight: 700, textTransform: 'uppercase' }}>{sec}{cur.stage !== 'linear' ? ` · ${cur.stage}` : ''}</span>
                    </div>
                    <TestTimer initialSeconds={s.time} onTimeUp={advance} sectionName="" />
                    <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                        <span style={{ fontSize: 14, opacity: .8 }}>Q <strong>{idxInSec + 1}</strong>/{secItems.length}</span>
                        <div style={{ height: 6, width: 100, background: '#ffffff18', borderRadius: 10, overflow: 'hidden' }}>
                            <div style={{ height: '100%', width: `${((idxInSec + 1) / secItems.length) * 100}%`, background: THEME.teal, transition: 'width .3s' }} />
                        </div>
                    </div>
                </div>
                {(sec === 'READING' && cur.task_type !== 'COMPLETE_THE_WORDS' && (cur.content?.title || cur.content?.headerText)) && (
                    <div style={{ width: '100%', padding: '20px 0', borderBottom: '1px solid #767676', textAlign: 'center', background: 'white' }}>
                        <h2 style={{ margin: 0, color: THEME.teal, fontSize: '26px', fontWeight: 'bold', fontFamily: 'Arial, Helvetica, sans-serif' }}>
                            {cur.content.title || cur.content.headerText}
                        </h2>
                    </div>
                )}
            </header>

            {/* MAIN */}
            <main style={{ flex: 1, overflowY: 'auto' }}>
                {renderItem(cur, handleNext, save, setAnswer, answers, sessionId)}
            </main>

            {/* FOOTER */}
            <footer style={{ background: 'white', padding: '16px 30px', borderTop: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0, boxShadow: '0 -4px 20px rgba(0,0,0,.03)' }}>
                <button onClick={() => { if (isReading && idxInSec > 0) setIdx(p => p - 1); }}
                    style={{ padding: '12px 24px', borderRadius: 8, border: '1px solid #e2e8f0', background: 'transparent', cursor: 'pointer', visibility: (isReading && idxInSec > 0) ? 'visible' : 'hidden' }}>← Previous</button>
                <button onClick={() => { if (isReading) setReviewing(true); }}
                    style={{ padding: '12px 24px', borderRadius: 8, border: '1px solid #e2e8f0', background: 'transparent', cursor: 'pointer', display: isReading ? 'block' : 'none' }}>Review</button>
                <button onClick={handleNext}
                    style={{ padding: '14px 44px', borderRadius: 8, border: 'none', background: THEME.teal, color: 'white', fontWeight: 700, fontSize: 16, cursor: 'pointer', boxShadow: `0 4px 0 ${THEME.tealDark}`, transition: 'transform .1s' }}
                    onMouseDown={e => e.currentTarget.style.transform = 'translateY(2px)'}
                    onMouseUp={e => e.currentTarget.style.transform = 'translateY(0)'}
                >{idx === items.length - 1 ? 'FINISH TEST' : 'NEXT →'}</button>
            </footer>

            {/* LISTENING CONFIRM */}
            {confirming && (
                <Overlay>
                    <div style={{ background: 'white', padding: 40, borderRadius: 16, maxWidth: 400, textAlign: 'center', boxShadow: '0 20px 50px rgba(0,0,0,.3)' }}>
                        <div style={{ fontSize: 40, marginBottom: 16 }}>⚠️</div>
                        <h3 style={{ fontSize: 20, fontWeight: 700, marginBottom: 8 }}>Confirm</h3>
                        <p style={{ color: '#64748b', fontSize: 15, lineHeight: 1.5, marginBottom: 28 }}>You cannot return to this question.</p>
                        <div style={{ display: 'flex', gap: 12 }}>
                            <button onClick={() => setConfirming(false)} style={{ flex: 1, padding: 12, border: '1px solid #e2e8f0', background: 'transparent', borderRadius: 8, cursor: 'pointer' }}>Wait</button>
                            <button onClick={() => { setConfirming(false); advance(); }} style={{ flex: 1, padding: 12, border: 'none', background: THEME.teal, color: 'white', fontWeight: 600, borderRadius: 8, cursor: 'pointer' }}>Proceed</button>
                        </div>
                    </div>
                </Overlay>
            )}

            {/* READING REVIEW */}
            {reviewing && (
                <Overlay>
                    <div style={{ background: 'white', width: '90%', maxWidth: 600, maxHeight: '80vh', padding: 30, borderRadius: 20, display: 'flex', flexDirection: 'column' }}>
                        <h2 style={{ marginBottom: 20, fontWeight: 700, fontSize: 22 }}>Review — {s.label}</h2>
                        <div style={{ flex: 1, overflowY: 'auto', display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 10 }}>
                            {secItems.map((item, i) => {
                                const isAns = item.questions?.[0]?.id ? !!answers[item.questions[0].id] : !!answers[item.id];
                                return (
                                    <button key={item.id} onClick={() => { setIdx(items.indexOf(item)); setReviewing(false); }}
                                        style={{ padding: '16px 8px', borderRadius: 10, border: '1px solid', borderColor: isAns ? THEME.teal : '#e2e8f0', background: isAns ? THEME.tealLight : 'transparent', color: isAns ? THEME.teal : '#94a3b8', fontWeight: 700, cursor: 'pointer', fontSize: 14 }}
                                    >{i + 1}</button>
                                )
                            })}
                        </div>
                        <button onClick={() => setReviewing(false)} style={{ marginTop: 20, padding: 14, border: 'none', background: THEME.navy, color: 'white', borderRadius: 10, fontWeight: 600, cursor: 'pointer' }}>Close</button>
                    </div>
                </Overlay>
            )}
        </div>
    );
};

/* ── tiny sub-components ──────────────────────────────────────────────── */

const Overlay: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,.8)', backdropFilter: 'blur(6px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
        {children}
    </div>
);

const StatBox: React.FC<{ label: string; value: string | number; highlight?: boolean }> = ({ label, value, highlight }) => (
    <div style={{ background: highlight ? THEME.teal : 'rgba(255,255,255,.1)', padding: '14px 24px', borderRadius: 12, minWidth: 90 }}>
        <div style={{ fontSize: 11, opacity: .6, marginBottom: 4 }}>{label}</div>
        <div style={{ fontSize: 22, fontWeight: 700 }}>{value}</div>
    </div>
);

/* ══════════════════════════════════════════════════════════════════════════
   ITEM RENDERER
   ══════════════════════════════════════════════════════════════════════════ */
function renderItem(item: ParsedItem, onNext: () => void, save: (data: Record<string, any>) => void, setAnswer: (k: string, v: string) => void, answers: Record<string, string>, sessionId: string | null): React.ReactNode {
    const c = item.content;
    switch (item.task_type) {
        case 'COMPLETE_THE_WORDS': {
            const raw = c.text || c.stimulus || '';
            let wi = 0;
            const initAnswers: Record<string, string> = {};
            const stim = raw.replace(/(\S*?)(_+)(\S*)/g, (_m: string, p: string, u: string, s: string) => {
                const wid = `w${wi}`;
                const questionId = item.questions?.[wi]?.id;
                if (questionId && answers[questionId]) {
                    initAnswers[wid] = answers[questionId];
                }
                wi++;
                return `${p}{${wid}:${u.length}}${s}`;
            });
            return <ClozeParagraph key={item.id} stimulusText={stim} initialAnswers={initAnswers} onWordComplete={(id, v) => {
                const qi = parseInt(id.replace('w', ''));
                const questionId = item.questions?.[qi]?.id;
                if (questionId) setAnswer(questionId, String(v));
                else save({ [id]: v });
            }} />;
        }
        case 'READ_IN_DAILY_LIFE':
            return (
                <ReadInDailyLife stimulusText={c.text || ''} headerText={c.title || 'Notice'} stimulusType={c.type || 'notice'} contentObj={c}>
                    <div style={{ padding: 20 }}>{renderMCQs(c.questions, item, save, setAnswer, answers)}</div>
                </ReadInDailyLife>
            );
        case 'READ_ACADEMIC_PASSAGE': {
            let targetWord = '';
            const qtext = item.questions?.[0]?.question_text || c.questions?.[0]?.question_text || '';
            const match = qtext.match(/word\s+["“”'‘]([^"“”'‘]+)["“”'‘]\s+in the passage/i);
            if (match && match[1]) {
                targetWord = match[1].trim();
            }
            return (
                <ReadAcademicPassage title={c.title || 'Academic Reading'} content={c.text || ''} targetWord={targetWord}>
                    <div style={{ padding: 20 }}>{renderMCQs(c.questions, item, save, setAnswer, answers)}</div>
                </ReadAcademicPassage>
            );
        }
        case 'LISTEN_CHOOSE_RESPONSE':
            return <ListenChooseResponse audioUrl={c.audio_url ? `/${c.audio_url}` : ''} options={c.questions?.[0]?.options || []} speakerImageUrl={c.speakerImageUrl || "/images/speaker_unisex.png"} onOptionSelect={i => item.questions?.[0]?.id ? setAnswer(item.questions[0].id, String(i)) : save({ answer: i })} />;
        case 'LISTEN_CONVERSATION':
            return <ListenConversation audioUrl={c.audio_url ? `/${c.audio_url}` : ''} questionText={c.questions?.[0]?.question_text || ''} options={c.questions?.[0]?.options || []} speakerImageUrl={c.speakerImageUrl || "/images/speaker_conversation.png"} onOptionSelect={i => item.questions?.[0]?.id ? setAnswer(item.questions[0].id, String(i)) : save({ answer: i })} />;
        case 'LISTEN_ANNOUNCEMENT':
            return <ListenAnnouncement audioUrl={c.audio_url ? `/${c.audio_url}` : ''} questionText={c.questions?.[0]?.question_text || ''} options={c.questions?.[0]?.options || []} speakerImageUrl={c.speakerImageUrl || "/images/speaker_unisex.png"} onOptionSelect={i => item.questions?.[0]?.id ? setAnswer(item.questions[0].id, String(i)) : save({ answer: i })} />;
        case 'LISTEN_ACADEMIC_TALK':
            return <ListenAcademicTalk audioUrl={c.audio_url ? `/${c.audio_url}` : ''} questionText={c.questions?.[0]?.question_text || ''} options={c.questions?.[0]?.options || []} speakerImageUrl={c.speakerImageUrl || "/images/speaker_unisex.png"} onOptionSelect={i => item.questions?.[0]?.id ? setAnswer(item.questions[0].id, String(i)) : save({ answer: i })} />;
        case 'BUILD_A_SENTENCE': {
            // Shuffle the fragments once using a deterministic or stored random
            const original = c.fragments || [];
            // Basic seeded/reproducible shuffle by hash or just simple random for now
            // To prevent hydration/rerender bouncing, we use the string length as a mock seed
            const pseudoScramble = [...original].sort((a, b) => (a.length * b.length % 3) - 1);

            return <div style={{ padding: 40 }}>
                <BuildSentence
                    contextSpeakerUrl="/images/placeholder_user.png"
                    builderSpeakerUrl="/images/placeholder_user.png"
                    prefixText={c.prefixText || ""}
                    contextText={c.context || ''}
                    scrambledWords={pseudoScramble.length ? pseudoScramble : original}
                    suffixText={c.endPunctuation || "."}
                    onSentenceUpdate={o => {
                        const qid = item.questions?.[0]?.id;
                        if (qid) setAnswer(qid, JSON.stringify(o));
                        else save({ order: o });
                    }}
                /></div>;
        }
        case 'WRITE_AN_EMAIL': {
            const bulletsHtml = (c.bullets || []).map((b: string) => `<li style="margin-bottom:6px;">${b}</li>`).join('');
            const emailPromptHtml = `
                <div style="font-family: Arial, sans-serif; font-size: 16px;">
                    <h3 style="margin-top:0; color:#005587;">Directions:</h3>
                    <p style="margin-bottom:20px;">Read the scenario below and write an email to the specified recipient.</p>
                    <h3 style="color:#005587;">Scenario:</h3>
                    <p style="margin-bottom:20px; line-height:1.5;">${c.scenario || ''}</p>
                    <h3 style="color:#005587;">Your email should do the following:</h3>
                    <ul style="margin-left: 20px; line-height: 1.5;">${bulletsHtml}</ul>
                </div>
            `;
            return <WriteEmail promptHTML={emailPromptHtml} onSave={t => setAnswer(item.id, t)} emailSubject={c.topic || ''} emailTo={c.emailTo || ''} />;
        }
        case 'WRITE_ACADEMIC_DISCUSSION':
            return <WriteAcademicDiscussion professorPromptHTML={c.professor_prompt || ''} studentPosts={[{ id: '1', authorName: c.student_1_name || 'A', text: c.student_1_response || '' }, { id: '2', authorName: c.student_2_name || 'B', text: c.student_2_response || '' }]} onSave={t => setAnswer(item.id, t)} />;
        case 'LISTEN_AND_REPEAT': {
            const audioPath = c.sentences?.[0]?.audio_url || item.questions?.[0]?.question_audio_url || c.questions?.[0]?.question_audio_url || '';
            const audioUrl = audioPath ? (audioPath.startsWith('/') ? audioPath : '/' + audioPath) : '';

            // Map title to relevant image, or use fallback
            let targetImage = "/images/listen_repeat_zoo_sample.jpg";
            const title = (c.title || "").toLowerCase();

            if (title.includes("library") && !title.includes("checkout")) {
                targetImage = "/images/lib_listen_repeat_1772228106428.png";
            } else if (title.includes("campus") || title.includes("university")) {
                targetImage = "/images/campus_listen_repeat_1772228117050.png";
            } else if (title.includes("cafeteria") || title.includes("dining")) {
                targetImage = "/images/cafeteria_listen_repeat_1772228130534.png";
            } else if (title.includes("lab") || title.includes("biology") || title.includes("science")) {
                targetImage = "/images/lab_listen_repeat_1772228142114.png";
            } else if (title.includes("dormitory") || title.includes("hotel") || title.includes("desk")) {
                targetImage = "/images/dormitory_listen_repeat_1772228152329.png";
            } else if (title.includes("museum") || title.includes("art")) {
                targetImage = "/images/museum_listen_repeat_1772228165654.png";
            } else if (title.includes("gym") || title.includes("fitness") || title.includes("trainer")) {
                targetImage = "/images/gym_listen_repeat_1772228177297.png";
            } else if (title.includes("nature") || title.includes("park") || title.includes("reserve")) {
                targetImage = "/images/nature_listen_repeat_1772228188966.png";
            } else if (title.includes("club") || title.includes("fair") || title.includes("student")) {
                targetImage = "/images/club_listen_repeat_1772228200771.png";
            } else if (title.includes("bookstore") || title.includes("supplies")) {
                targetImage = "/images/bookstore_listen_repeat_1772228212526.png";
            } else if (title.includes("office") || title.includes("professor")) {
                targetImage = "/images/office_listen_repeat_1772228224438.png";
            }

            return <ListenRepeat
                imageUrl={targetImage}
                imageAlt={c.title || "Speaking"}
                audioUrl={audioUrl}
                questionId={item.questions?.[0]?.id || item.id}
                sessionId={sessionId || 'demo_session'}
                uploadUrl={`${API_BASE_URL}/api/audio/upload`}
                onComplete={onNext}
            />;
        }
        case 'TAKE_AN_INTERVIEW': {
            const audioPath = c.audio_url || c.questions?.[0]?.audio_url || c.questions?.[0]?.audioUrl || '';
            const audioUrl = audioPath ? (audioPath.startsWith('/') || audioPath.startsWith('http') ? audioPath : '/' + audioPath) : '';
            return <InterviewUI
                promptAudioUrl={audioUrl}
                imageUrl={c.speakerImageUrl || "/images/speaker_unisex.png"}
                maxRecordTimeSeconds={45}
                uploadUrl={`${API_BASE_URL}/api/audio/upload`}
                questionId={item.questions?.[0]?.id || item.id}
                sessionId={sessionId || 'demo_session'}
                onComplete={onNext}
            />;
        }
        default:
            return <div style={{ padding: 80, textAlign: 'center' }}>Unknown: <strong>{item.task_type}</strong></div>;
    }
}

function renderMCQs(questions: any[], item: ParsedItem, save: (data: any) => void, setAnswer: (k: string, v: string) => void, answers: Record<string, string>) {
    if (!questions) return null;
    return questions.map((q: any, qi: number) => {
        const questionId = item.questions?.[qi]?.id || `${item.id}-${qi}`;
        return (
            <div key={qi} style={{ marginBottom: 28 }}>
                {q.question_text && <p style={{ fontWeight: 700, marginBottom: 14 }}>{q.question_text.replace(/^\d+\.\s*/, '')}</p>}
                {(q.options || []).map((opt: string, oi: number) => (
                    <label key={oi} style={{ display: 'block', padding: 12, border: '1px solid #e2e8f0', borderRadius: 8, marginBottom: 8, cursor: 'pointer', transition: 'background .15s' }}
                        onMouseEnter={e => e.currentTarget.style.background = '#f1f5f9'}
                        onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                    >
                        <input type="radio" name={`q-${questionId}`} checked={answers[questionId] === String(oi) || answers[`q${qi}_answer`] === String(oi)} onChange={() => {
                            if (item.questions?.[qi]?.id) {
                                setAnswer(questionId, String(oi));
                            } else {
                                save({ [`q${qi}_answer`]: oi });
                            }
                        }} style={{ marginRight: 10 }} />{opt}
                    </label>
                ))}
            </div>
        );
    });
}
