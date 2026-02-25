'use client';

import React, { useState } from 'react';
import { ClozeParagraph } from '../../../../components/ClozeParagraph';
const passage = {
    "text": "We know from drawings that have been preserved in caves for over 10,000 years that early humans performed dances as a group activity. We mi_ _ _ think th_ _ prehistoric peo_ _ _ concentrated on_ _ on ba_ _ _ survival. How_ _ _ _, it i_ clear fr_ _ the rec_ _ _ that dan_ _ _ _ was important to them. They recorded more drawings of dances than of any other group activity. Dances served various purposes, including ritualistic communication with the divine, storytelling, and social cohesion.",
    "gaps": [
        { "position": "mi_ _ _", "answer": "might", "wordIndex": 0 },
        { "position": "th_ _", "answer": "that", "wordIndex": 1 },
        { "position": "peo_ _ _", "answer": "people", "wordIndex": 2 },
        { "position": "concentrated on_ _", "answer": "only", "wordIndex": 3 },
        { "position": "ba_ _ _", "answer": "basic", "wordIndex": 4 },
        { "position": "How_ _ _ _,", "answer": "However,", "wordIndex": 5 },
        { "position": "i_", "answer": "is", "wordIndex": 6 },
        { "position": "fr_ _", "answer": "from", "wordIndex": 7 },
        { "position": "rec_ _ _", "answer": "record", "wordIndex": 8 },
        { "position": "dan_ _ _ _", "answer": "dances", "wordIndex": 9 }
    ]
};

function formatStimulus(text: string, gaps: any[]) {
    let formattedText = text;
    gaps.forEach((gap, index) => {
        const numUnderscores = (gap.position.match(/_/g) || []).length;
        const formattedGap = gap.position.replace(/(_\s*)+/, `{${gap.wordIndex}:${numUnderscores}}`);
        formattedText = formattedText.replace(gap.position, formattedGap);
    });
    return formattedText;
}

export default function ReadingTweakPage() {
    const testStimulus = formatStimulus(passage.text, passage.gaps);
    const [words, setWords] = useState<Record<string, string>>({});

    const handleWordComplete = (id: string, val: string) => {
        setWords(prev => ({ ...prev, [id]: val }));
    };

    return (
        <div style={{ padding: '40px', maxWidth: '800px', margin: '0 auto', fontFamily: 'Arial, Helvetica, sans-serif' }}>
            <h1 style={{ color: '#005587', marginBottom: '20px' }}>Physics Sandbox: Complete the Words</h1>
            <p style={{ color: '#5E6A75', marginBottom: '30px' }}>
                This is an isolated sandbox to test the exact ETS interaction physics for the Reading section.<br />
                Try typing, backspacing, typing invalid characters, and reaching the end of a word to trigger auto-advance.
            </p>

            <div style={{ backgroundColor: '#F4F5F7', padding: '30px', borderRadius: '8px', border: '1px solid #D1D6E0' }}>
                <ClozeParagraph
                    stimulusText={testStimulus}
                    onWordComplete={handleWordComplete}
                />
            </div>

            <div style={{ marginTop: '40px', padding: '20px', backgroundColor: '#FFFFFF', border: '1px solid #D1D6E0', borderRadius: '8px' }}>
                <h3 style={{ margin: '0 0 15px 0' }}>Live State Tracker</h3>
                <pre style={{ fontSize: '14px', color: '#D32F2F' }}>
                    {JSON.stringify(words, null, 2)}
                </pre>
            </div>
        </div>
    );
}
