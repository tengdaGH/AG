'use client';

import React from 'react';

export default function AudioShowcase() {
    const audios = [
        { id: 'LR1', name: 'LR 1', url: '/audio/test/lr_1.mp3', text: 'The professor will hold extra office hours in the student lounge tomorrow afternoon.' },
        { id: 'LR2', name: 'LR 2', url: '/audio/test/lr_2.mp3', text: 'Scientific research often requires a significant investment of both time and financial resources.' },
        { id: 'LR3', name: 'LR 3', url: '/audio/test/lr_3.mp3', text: 'Please remember to submit your final research paper through the online portal by Friday at noon.' },
        { id: 'LR4', name: 'LR 4', url: '/audio/test/lr_4.mp3', text: 'The university library recently updated its collection of digital journals and primary sources.' },
        { id: 'LR5', name: 'LR 5', url: '/audio/test/lr_5.mp3', text: 'Biological organisms must adapt to their environment in order to survive and reproduce effectively.' },
        { id: 'C1', name: 'Student', url: '/audio/test/conv_student.mp3', text: 'Hi Professor, I was wondering if you had a moment to discuss my paper topic?' },
        { id: 'C2', name: 'Professor', url: '/audio/test/conv_professor.mp3', text: 'Of course. Why don\'t you come into my office and we can go over your initial draft?' },
        { id: 'CODE', name: 'SSML Readout (1.5-mini)', url: '/audio/test/ssml_code_readout.mp3', text: 'This audio now uses correct SSML interpretation. You should hear half a second of silence at the beginning and then this sentence, without any tags being read out loud.' },
    ];

    return (
        <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto', fontFamily: 'sans-serif' }}>
            <h1 style={{ color: '#1e293b', marginBottom: '1.5rem' }}>Inworld Audio Generation Test</h1>
            <p style={{ color: '#64748b', marginBottom: '2rem' }}>Generated 5 LR questions and a short conversation snippet.</p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                {audios.map((audio) => (
                    <div key={audio.id} style={{ padding: '1.5rem', border: '1px solid #e2e8f0', borderRadius: '12px', backgroundColor: '#fff', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
                        <div style={{ fontWeight: 600, marginBottom: '0.5rem', color: '#334155' }}>
                            {audio.name}
                        </div>
                        <div style={{ fontSize: '0.875rem', fontStyle: 'italic', color: '#4b5563', marginBottom: '1rem' }}>"{audio.text}"</div>

                        <audio controls style={{ width: '100%' }}>
                            <source src={audio.url} type="audio/mpeg" />
                            Your browser does not support the audio element.
                        </audio>
                    </div>
                ))}
            </div>
        </div>
    );
}
