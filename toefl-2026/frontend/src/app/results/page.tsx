'use client';

import React, { useEffect, useState } from 'react';
import { useTestStore } from '../../store/testStore';
import { ScoreReportDashboard } from '../../components/ScoreReportDashboard';
import { useRouter } from 'next/navigation';
import { API_BASE_URL } from '../../lib/api-config';

export default function ResultsPage() {
    const sessionId = useTestStore(state => state.sessionId);
    const router = useRouter();
    const [results, setResults] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        if (!sessionId) {
            // Uncomment to force redirect to home if no session
            // router.push('/');
            // For dev/demo testing, if no sessionId, we might just mock it
        }

        async function fetchResults() {
            if (!sessionId) {
                // If there's no session id from the store (e.g. direct nav to /results), display fallback
                setLoading(false);
                return;
            }
            try {
                const res = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/results`, {
                    headers: { 'Bypass-Tunnel-Reminder': 'true' }
                });
                if (!res.ok) throw new Error('Failed to load results');
                const data = await res.json();
                setResults(data);
            } catch (err: any) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        }

        fetchResults();
    }, [sessionId, router]);

    if (loading) {
        return (
            <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#f8fafc' }}>
                <div style={{ textAlign: 'center' }}>
                    <div style={{
                        width: '50px', height: '50px', border: '4px solid #00558744',
                        borderTopColor: '#005587', borderRadius: '50%',
                        animation: 'spin 1s linear infinite', margin: '0 auto 20px'
                    }} />
                    <h2 style={{ color: '#005587', fontFamily: 'sans-serif' }}>Generating Official Report...</h2>
                    <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <h2 style={{ color: '#D32F2F', fontFamily: 'sans-serif' }}>Error: {error}</h2>
            </div>
        );
    }

    // Default mock data if no sessionId is available or API failed but we still want to show the UI
    const finalScores = results?.scores || {
        reading: { band: 4.5, cefr: 'B2', legacyRange: '24-27' },
        listening: { band: 4.0, cefr: 'B2', legacyRange: '24-27' },
        speaking: { band: 3.5, cefr: 'B2', legacyRange: '18-23' },
        writing: { band: 4.0, cefr: 'B2', legacyRange: '24-27' },
        total: { band: 4.0, cefr: 'B2', legacyRange: '90-104 / 120' }
    };

    const finalFeedback = results?.feedback || {
        reading: "No data submitted.",
        writing: "No data submitted."
    };

    const demoMyBest = {
        reading: { band: 5.0, date: 'Oct 12, 2025' },
        listening: { band: 4.5, date: 'Nov 04, 2025' },
        speaking: { band: 4.0, date: 'Jan 10, 2026' },
        writing: { band: 4.5, date: 'Feb 20, 2026' },
        total: 4.5
    };

    return (
        <div style={{ backgroundColor: '#f8fafc', minHeight: '100vh', padding: '40px 0' }}>
            <ScoreReportDashboard
                candidateName="ETS Candidate"
                etsId="TOEFL-2026-X8Y9"
                testDate={new Date().toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' })}
                scores={finalScores}
                feedback={finalFeedback}
                myBest={demoMyBest}
                detailedResponses={results?.detailedResponses}
            />
        </div>
    );
}
