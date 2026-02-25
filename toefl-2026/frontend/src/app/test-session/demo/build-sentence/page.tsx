'use client';

import React, { useState } from 'react';
import { BuildSentence } from '../../../../components/BuildSentence';

export default function BuildSentenceDemoPage() {
    const [sentenceOrder, setSentenceOrder] = useState<string[]>([]);

    // Placeholder images for now
    const contextSpeakerUrl = '/images/speakers/female.png';
    const builderSpeakerUrl = '/images/speakers/male.png';

    const contextText = "What was the highlight of your trip?";
    const scrambledWords = ["were", "the", "was", "old city", "showed us around", "who", "tour guides"];
    const prefixText = "The";
    const suffixText = "fantastic.";

    return (
        <div style={{ padding: '40px', maxWidth: '1200px', height: '80vh', margin: '0 auto', fontFamily: 'Arial, Helvetica, sans-serif' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h1 style={{ color: '#005587', margin: 0 }}>Physics Sandbox: Build a Sentence</h1>
            </div>
            <p style={{ color: '#5E6A75', marginBottom: '30px' }}>
                This verifies the drag-and-drop physics of the 'Build a Sentence' writing task using @dnd-kit/core to simulate word reordering slots, matching the native ETS layout with circular speaker context portraits.
            </p>

            <div style={{ border: '1px solid #767676', backgroundColor: '#FFFFFF', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
                <BuildSentence
                    contextSpeakerUrl={contextSpeakerUrl}
                    contextText={contextText}
                    builderSpeakerUrl={builderSpeakerUrl}
                    prefixText={prefixText}
                    suffixText={suffixText}
                    scrambledWords={scrambledWords}
                    onSentenceUpdate={setSentenceOrder}
                />
            </div>
        </div>
    );
}
