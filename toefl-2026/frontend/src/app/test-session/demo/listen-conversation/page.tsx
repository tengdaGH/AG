'use client';

import React, { useState } from 'react';
import { ListenConversation } from '../../../../components/ListenConversation';

export default function ListenConversationDemoPage() {
    const [selectedOptionIndex, setSelectedOptionIndex] = useState<number | null>(null);

    // Dynamic generated asset from the Antigravity engine
    const speakerImageUrl = `/images/speakers/conversation.png`;

    const questionText = "What does the woman imply that she was about to do?";

    const options = [
        "See a play",
        "Change her clothes",
        "Go shopping",
        "Eat dinner"
    ];

    // Dummy audio URL so it finishes immediately and fades in options
    const dummyAudio = "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=";

    return (
        <div style={{ padding: '40px', maxWidth: '1200px', height: '80vh', margin: '0 auto', fontFamily: 'Arial, Helvetica, sans-serif' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h1 style={{ color: '#005587', margin: 0 }}>Physics Sandbox: Listen to a Conversation</h1>
            </div>
            <p style={{ color: '#5E6A75', marginBottom: '30px' }}>
                This verifies the "Listen to a Conversation" task correctly mirrors the ETS 50/50 split-screen layout, bringing over the visible question text, the thick black top border, and dual-speaker context mapping.
            </p>

            <div style={{ height: '550px', border: '1px solid #767676', backgroundColor: '#FFFFFF', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
                <ListenConversation
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
