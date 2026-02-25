'use client';

import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/Card';
import { Button } from '@/components/Button';
import { Input } from '@/components/Input';

export default function ItemBankDesigner() {
    const [sectionType, setSectionType] = useState('READING');
    const [targetCEFR, setTargetCEFR] = useState('B2');
    const [difficulty, setDifficulty] = useState('0.5');
    const [discrimination, setDiscrimination] = useState('1.0');

    // Basic mock saving
    const handleSave = () => {
        alert('Item saved to PostgreSQL! Item marked as "Draft" pending Psychometrician review.');
        window.location.href = '/dashboard/admin';
    };

    return (
        <div className="app-layout" style={{ backgroundColor: 'var(--background)' }}>
            <header style={{ padding: '1rem 2rem', borderBottom: '1px solid var(--border-color)', backgroundColor: 'var(--card-bg)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{ width: '32px', height: '32px', backgroundColor: '#ef4444', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 'bold' }}>A</div>
                    <span style={{ fontWeight: 600, fontSize: '1.25rem' }}>Item Bank Designer</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <Button variant="ghost" size="sm" onClick={() => window.location.href = '/dashboard/admin'}>Back to Admin</Button>
                    <Button size="sm" onClick={handleSave}>Save as Draft</Button>
                </div>
            </header>

            <main className="container" style={{ paddingTop: '2rem', paddingBottom: '2rem', display: 'flex', gap: '2rem', maxWidth: '1400px' }}>

                {/* Left Column: Metadata & Settings */}
                <div style={{ width: '350px', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                    <Card>
                        <CardHeader>
                            <CardTitle>Item Metadata</CardTitle>
                        </CardHeader>
                        <CardContent style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                            <div>
                                <label style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--foreground)', display: 'block', marginBottom: '0.375rem' }}>Section Type</label>
                                <select
                                    value={sectionType}
                                    onChange={(e) => setSectionType(e.target.value)}
                                    style={{ width: '100%', height: '2.5rem', borderRadius: '6px', border: '1px solid var(--border-color)', padding: '0 0.75rem', backgroundColor: 'var(--card-bg)' }}
                                >
                                    <option value="READING">Reading (Multi-Stage Adaptive)</option>
                                    <option value="LISTENING">Listening (Multi-Stage Adaptive)</option>
                                    <option value="SPEAKING">Speaking (Virtual Interview)</option>
                                    <option value="WRITING">Writing (Write an Email)</option>
                                </select>
                            </div>

                            <div>
                                <label style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--foreground)', display: 'block', marginBottom: '0.375rem' }}>Target CEFR Level</label>
                                <select
                                    value={targetCEFR}
                                    onChange={(e) => setTargetCEFR(e.target.value)}
                                    style={{ width: '100%', height: '2.5rem', borderRadius: '6px', border: '1px solid var(--border-color)', padding: '0 0.75rem', backgroundColor: 'var(--card-bg)' }}
                                >
                                    <option value="A2">A2 (Entry)</option>
                                    <option value="B1">B1 (Intermediate)</option>
                                    <option value="B2">B2 (Upper Intermediate)</option>
                                    <option value="C1">C1 (Advanced)</option>
                                    <option value="C2">C2 (Mastery)</option>
                                </select>
                            </div>

                            <div style={{ paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
                                <h4 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '1rem', color: 'var(--text-muted)' }}>IRT PARAMETERS (3PL MODEL)</h4>
                                <Input
                                    label="Difficulty (b-parameter)"
                                    type="number"
                                    step="0.1"
                                    min="-3.0"
                                    max="3.0"
                                    value={difficulty}
                                    onChange={(e) => setDifficulty(e.target.value)}
                                    helperText="Range: -3.0 (Easy) to +3.0 (Hard)"
                                />
                                <Input
                                    label="Discrimination (a-parameter)"
                                    type="number"
                                    step="0.1"
                                    min="0.5"
                                    max="2.5"
                                    value={discrimination}
                                    onChange={(e) => setDiscrimination(e.target.value)}
                                    helperText="Range: 0.5 (Low) to 2.5 (High)"
                                />
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle>AI Content Generation</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                                Use the Item Architect to automatically ingest legacy TPO files and rewrite them to fit the 2026 adaptive format block size.
                            </p>
                            <Button variant="secondary" fullWidth style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', justifyContent: 'center' }}>
                                <span>✨ Generate via Scraped TPO</span>
                            </Button>
                        </CardContent>
                    </Card>
                </div>

                {/* Right Column: Content Editor */}
                <div style={{ flex: 1 }}>
                    <Card style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                        <CardHeader style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '1.5rem', backgroundColor: '#f8fafc' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <CardTitle>Content Editor</CardTitle>
                                <div style={{ display: 'flex', gap: '0.5rem' }}>
                                    <Button variant="ghost" size="sm">Markdown</Button>
                                    <Button variant="secondary" size="sm">Preview</Button>
                                </div>
                            </div>
                        </CardHeader>
                        <CardContent style={{ flex: 1, padding: 0, display: 'flex', flexDirection: 'column' }}>
                            <div style={{ padding: '1.5rem', flex: 1 }}>
                                <label style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--foreground)', display: 'block', marginBottom: '0.5rem' }}>Prompt / Passage Reading Area</label>
                                <textarea
                                    placeholder="Enter the reading passage, listening transcript, or writing prompt scenario here..."
                                    style={{
                                        width: '100%',
                                        height: '250px',
                                        padding: '1rem',
                                        borderRadius: '6px',
                                        border: '1px solid var(--border-color)',
                                        resize: 'vertical',
                                        fontFamily: 'var(--font-mono)',
                                        fontSize: '0.875rem',
                                        lineHeight: 1.6,
                                        backgroundColor: 'var(--card-bg)'
                                    }}
                                />

                                <div style={{ marginTop: '2rem' }}>
                                    <label style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--foreground)', display: 'block', marginBottom: '0.5rem' }}>Question Target</label>
                                    <Input
                                        placeholder="e.g. According to paragraph 2, why did..."
                                        fullWidth
                                    />
                                </div>

                                <div style={{ marginTop: '1.5rem' }}>
                                    <label style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--foreground)', display: 'block', marginBottom: '0.5rem' }}>Multiple Choice Options (Optional)</label>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                                        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                                            <input type="radio" name="correct" defaultChecked />
                                            <Input placeholder="Correct Answer..." fullWidth style={{ marginBottom: 0 }} />
                                        </div>
                                        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                                            <input type="radio" name="correct" />
                                            <Input placeholder="Distractor 1..." fullWidth style={{ marginBottom: 0 }} />
                                        </div>
                                        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                                            <input type="radio" name="correct" />
                                            <Input placeholder="Distractor 2..." fullWidth style={{ marginBottom: 0 }} />
                                        </div>
                                        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                                            <input type="radio" name="correct" />
                                            <Input placeholder="Distractor 3..." fullWidth style={{ marginBottom: 0 }} />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>

            </main>
        </div>
    );
}
