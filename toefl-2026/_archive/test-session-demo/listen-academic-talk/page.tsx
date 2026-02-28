'use client';

import React, { useState } from 'react';
import { ListenAcademicTalk } from '../../../../components/ListenAcademicTalk';

export default function ListenAcademicTalkDemoPage() {
    const [selectedOptionIndex, setSelectedOptionIndex] = useState<number | null>(null);

    // Dynamic generated asset mapping to the exact spec
    const speakerImageUrl = `/images/speakers/academic_talk.png`;

    const questionText = "What does the speaker say about her walk in the park?";

    const options = [
        "It is similar to her experience watching a good movie.",
        "Her mind has space for thoughts unrelated to nature.",
        "She needs to put in special effort to stay focused on flowers and trees.",
        "She gets mental fatigue from her mind engaging in hard fascination."
    ];

    // Dummy audio URL so it finishes immediately and fades in options
    const dummyAudio = "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=";

    return (
        <div style={{ padding: '40px', maxWidth: '1200px', height: '80vh', margin: '0 auto', fontFamily: 'Arial, Helvetica, sans-serif' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h1 style={{ color: '#005587', margin: 0 }}>Physics Sandbox: Listen to an Academic Talk</h1>
            </div>
            <p style={{ color: '#5E6A75', marginBottom: '30px' }}>
                This verifies the "Listen to an Academic Talk" task correctly mirrors the ETS 50/50 split-screen layout, bringing over the visible question text, standard bounded border, and single-educator context mapping.
            </p>

            <div style={{ height: '550px', backgroundColor: '#FFFFFF', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
                <ListenAcademicTalk
                    audioUrl={dummyAudio}
                    questionText={questionText}
                    options={options}
                    speakerImageUrl={speakerImageUrl}
                    onOptionSelect={(idx) => setSelectedOptionIndex(idx)}
                />
            </div>
        </div>
    );
}
