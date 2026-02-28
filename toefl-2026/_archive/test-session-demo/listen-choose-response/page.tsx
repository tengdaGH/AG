'use client';

import React, { useState } from 'react';
import { ListenChooseResponse } from '../../../../components/ListenChooseResponse';

export default function ListenChooseResponseDemoPage() {
    const [selectedOptionIndex, setSelectedOptionIndex] = useState<number | null>(null);
    const [speakerGender, setSpeakerGender] = useState<'female' | 'male'>('female');

    // Natively pulling from the Next.js public directory
    const speakerImageUrl = `/images/speakers/${speakerGender}.png`;

    const options = [
        "As a matter of fact, I was returning a book.",
        "Yes, you can find it in the reference section.",
        "I don't think I'll have enough time to do that.",
        "Actually, I think I can get there a little earlier."
    ];

    // We use a blank 1-second audio or dummy audio URL so it finishes immediately
    const dummyAudio = "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=";

    return (
        <div style={{ padding: '40px', maxWidth: '1200px', height: '80vh', margin: '0 auto', fontFamily: 'Arial, Helvetica, sans-serif' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h1 style={{ color: '#005587', margin: 0 }}>Physics Sandbox: Listen and Choose a Response</h1>
                <button
                    onClick={() => setSpeakerGender(prev => prev === 'female' ? 'male' : 'female')}
                    style={{ padding: '8px 16px', cursor: 'pointer', backgroundColor: '#005587', color: 'white', border: 'none', borderRadius: '4px' }}
                >
                    Toggle Speaker Gender (Current: {speakerGender})
                </button>
            </div>
            <p style={{ color: '#5E6A75', marginBottom: '30px' }}>
                This verifies that the single-speaker "Listen and Choose" task correctly mirrors the ETS 50/50 split-screen layout, bringing over the flat oval selections and teal header from the Reading architecture.
            </p>

            <div style={{ height: '550px', border: '1px solid #D1D6E0', borderRadius: '8px', overflow: 'hidden', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
                <ListenChooseResponse
                    audioUrl={dummyAudio}
                    options={options}
                    speakerImageUrl={speakerImageUrl}
                    onOptionSelect={(idx) => setSelectedOptionIndex(idx)}
                />
            </div>
        </div>
    );
}
