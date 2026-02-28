'use client';

import React, { useEffect, useState } from 'react';
import { API_BASE_URL } from '@/lib/api-config';

interface AuditData {
  total: number;
  by_section: Record<string, Record<string, number>>;
}

const SECTION_CONFIG = [
  {
    key: 'READING',
    label: 'Reading',
    icon: '📖',
    color: '#3b82f6',
    bg: 'rgba(59, 130, 246, 0.1)',
    duration: '35 min',
    questions: '20 questions',
    description: 'Academic passages, daily-life texts, and C-Test (Complete the Words) — testing comprehension at every level.',
    taskTypes: ['Read Academic Passage', 'Read in Daily Life', 'Complete the Words'],
    demoPath: '/test-session/demo',
  },
  {
    key: 'LISTENING',
    label: 'Listening',
    icon: '🎧',
    color: '#8b5cf6',
    bg: 'rgba(139, 92, 246, 0.1)',
    duration: '36 min',
    questions: '28 questions',
    description: 'Conversations, announcements, and academic talks — with single-play audio and adaptive routing.',
    taskTypes: ['Listen & Choose', 'Conversation', 'Announcement', 'Academic Talk'],
    demoPath: '/test-session/demo/listening',
  },
  {
    key: 'SPEAKING',
    label: 'Speaking',
    icon: '🎤',
    color: '#f59e0b',
    bg: 'rgba(245, 158, 11, 0.1)',
    duration: '16 min',
    questions: '4 tasks',
    description: 'Virtual interview and listen-and-repeat tasks — AI-scored pronunciation, fluency, and coherence.',
    taskTypes: ['Take an Interview', 'Listen and Repeat'],
    demoPath: '/test-session/demo/speaking',
  },
  {
    key: 'WRITING',
    label: 'Writing',
    icon: '✍️',
    color: '#10b981',
    bg: 'rgba(16, 185, 129, 0.1)',
    duration: '29 min',
    questions: '2 tasks',
    description: 'Email composition and academic discussion board — real-world writing with AI evaluation.',
    taskTypes: ['Write an Email', 'Academic Discussion', 'Build a Sentence'],
    demoPath: '/test-session/demo/writing',
  },
];

export default function Home() {
  const [audit, setAudit] = useState<AuditData | null>(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/items/audit`, {
      headers: { 'Bypass-Tunnel-Reminder': 'true' },
    })
      .then(res => res.ok ? res.json() : null)
      .then(data => data && setAudit(data))
      .catch(() => { });
  }, []);

  const getSectionCount = (sectionKey: string): number => {
    if (!audit?.by_section?.[sectionKey]) return 0;
    return Object.values(audit.by_section[sectionKey]).reduce((sum, n) => sum + n, 0);
  };

  const getTaskTypeCount = (): number => {
    if (!audit?.by_section) return 0;
    return Object.values(audit.by_section).reduce(
      (sum, types) => sum + Object.keys(types).length, 0
    );
  };

  return (
    <div className="landing-page">
      {/* ─── Navigation ─── */}
      <nav className="landing-nav">
        <a href="/" className="brand" style={{ textDecoration: 'none' }}>
          <div style={{
            width: '34px', height: '34px',
            background: 'linear-gradient(135deg, #2563eb, #7c3aed)',
            borderRadius: '10px',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff', fontWeight: 800, fontSize: '0.875rem',
          }}>T</div>
          TOEFL iBT 2026
        </a>
        <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
          <a href="/dashboard/admin/items" className="nav-links" style={{ color: 'var(--text-muted)', textDecoration: 'none', fontSize: '0.875rem', fontWeight: 500 }}>
            Admin
          </a>
          <a href="/test-session/full" className="btn btn-primary" style={{ padding: '0.5rem 1.25rem', fontSize: '0.8125rem' }}>
            Take Test
          </a>
        </div>
      </nav>

      {/* ─── Hero ─── */}
      <section className="landing-hero">
        <div className="hero-badge">
          <span className="pulse-dot" />
          New 2026 Format • Live Item Bank
        </div>
        <h1>Practice the Real<br />TOEFL iBT® Experience</h1>
        <p className="lead">
          The only practice platform built to the 2026 specification — adaptive routing,
          AI scoring, and every new task type, powered by
          {audit ? ` ${audit.total}+` : ''} real test items.
        </p>
        <div className="hero-ctas">
          <a href="/test-session/demo" className="btn btn-primary btn-lg">
            Start Practice Test
          </a>
          <a href="/test-session/full" className="btn btn-outline btn-lg">
            Full Simulated Test →
          </a>
        </div>
      </section>

      {/* ─── Stat Bar ─── */}
      {audit && (
        <div className="stat-bar">
          <div className="stat-item">
            <div className="stat-value">{audit.total}</div>
            <div className="stat-label">Total Items</div>
          </div>
          <div className="stat-item">
            <div className="stat-value">{getTaskTypeCount()}</div>
            <div className="stat-label">Task Types</div>
          </div>
          <div className="stat-item">
            <div className="stat-value">{Object.keys(audit.by_section).length}</div>
            <div className="stat-label">Sections</div>
          </div>
          <div className="stat-item">
            <div className="stat-value">116</div>
            <div className="stat-label">Minutes</div>
          </div>
        </div>
      )}

      {/* ─── Test Format Overview ─── */}
      <section className="landing-section">
        <h2>Test Format at a Glance</h2>
        <p className="section-subtitle">Four sections, adaptive difficulty, one sitting — roughly 2 hours.</p>
        <div className="format-grid">
          {SECTION_CONFIG.map(sec => (
            <div className="format-card" key={sec.key}>
              <div className="icon-circle" style={{ background: sec.bg, color: sec.color }}>
                {sec.icon}
              </div>
              <h3>{sec.label}</h3>
              <div className="format-meta">{sec.duration} • {sec.questions}</div>
              {audit && (
                <div className="pill" style={{ background: sec.bg, color: sec.color, borderColor: `${sec.color}30` }}>
                  {getSectionCount(sec.key)} items in bank
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* ─── Section Deep-Dive ─── */}
      <section className="landing-section">
        <h2>Explore Each Section</h2>
        <p className="section-subtitle">Every new 2026 task type — built and ready to practice.</p>
        <div className="section-cards-grid">
          {SECTION_CONFIG.map(sec => (
            <a href={sec.demoPath} className="section-deep-card" key={sec.key}>
              <div className="card-header-row">
                <div className="card-icon" style={{ background: sec.bg, color: sec.color }}>
                  {sec.icon}
                </div>
                <h3>{sec.label}</h3>
              </div>
              <div className="card-desc">{sec.description}</div>
              <div className="pill-row">
                {sec.taskTypes.map(tt => (
                  <span className="pill" key={tt}>{tt}</span>
                ))}
              </div>
              <span className="arrow-link">Practice now →</span>
            </a>
          ))}
        </div>
      </section>

      {/* ─── Footer ─── */}
      <footer className="landing-footer">
        Powered by Antigravity • TOEFL® is a registered trademark of ETS. This is an independent practice platform. • ©2026
      </footer>
    </div>
  );
}
