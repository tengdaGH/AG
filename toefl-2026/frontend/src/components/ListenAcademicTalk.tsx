'use client';

import React, { useState, useEffect, useRef } from 'react';

interface ListenAcademicTalkProps {
    audioUrl: string;
    questionText: string;
    options: string[];
    speakerImageUrl?: string;
    onOptionSelect: (index: number) => void;
}

export const ListenAcademicTalk: React.FC<ListenAcademicTalkProps> = ({
    audioUrl,
    questionText,
    options,
    speakerImageUrl,
    onOptionSelect
}) => {
    const [audioFinished, setAudioFinished] = useState(false);
    const [optionsVisible, setOptionsVisible] = useState(false);
    const [selectedOption, setSelectedOption] = useState<number | null>(null);
    const audioRef = useRef<HTMLAudioElement>(null);
    const timerRef = useRef<NodeJS.Timeout | null>(null);

    useEffect(() => {
        if (!audioRef.current) return;

        const showOptions = () => {
            setAudioFinished(true);
            timerRef.current = setTimeout(() => {
                setOptionsVisible(true);
            }, 200);
        };

        const handleEnded = () => showOptions();
        const handleError = () => showOptions();

        audioRef.current.addEventListener('ended', handleEnded);
        audioRef.current.addEventListener('error', handleError);
        audioRef.current.play().catch(() => {
            timerRef.current = setTimeout(showOptions, 2000);
        });

        const fallbackTimer = setTimeout(() => {
            if (!optionsVisible) showOptions();
        }, 3000);

        return () => {
            if (audioRef.current) {
                audioRef.current.removeEventListener('ended', handleEnded);
                audioRef.current.removeEventListener('error', handleError);
            }
            if (timerRef.current) clearTimeout(timerRef.current);
            clearTimeout(fallbackTimer);
        };
    }, []);

    const handleOptionSelect = (idx: number) => {
        setSelectedOption(idx);
        onOptionSelect(idx);
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', width: '100%', height: '100%', backgroundColor: '#FFFFFF', border: '1px solid #767676', fontFamily: 'Times New Roman, Times, serif' }}>


            {/* Split Screen Area (No thick top border for Academic Talk) */}
            <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
                {/* Left Pane: Audio Player */}
                <div style={{ flex: '1 1 50%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px', gap: '20px' }}>
                    {speakerImageUrl && (
                        <img
                            src={speakerImageUrl}
                            alt="Educator giving academic talk"
                            style={{ maxWidth: '100%', maxHeight: '300px', objectFit: 'contain' }}
                        />
                    )}
                    <audio ref={audioRef} src={audioUrl} controls style={{ width: '80%', maxWidth: '400px' }} />
                    <p style={{ color: '#767676', fontSize: '14px', margin: 0 }}>Listen to the talk, then answer the question.</p>
                </div>

                {/* Right Pane: Question and Options */}
                <div style={{ flex: '1 1 50%', display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '40px' }}>
                    <div style={{
                        opacity: optionsVisible ? 1 : 0,
                        pointerEvents: optionsVisible ? 'auto' : 'none',
                        transition: 'opacity 0.2s ease',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '24px'
                    }}>
                        {/* Visible Question Text directly above options */}
                        <h3 style={{ fontSize: '18px', color: '#212121', marginBottom: '8px', fontWeight: 'normal' }}>
                            {questionText}
                        </h3>

                        {options.map((opt, idx) => (
                            <label
                                key={idx}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    cursor: 'pointer'
                                }}
                            >
                                <input
                                    type="radio"
                                    name="listen_academic_talk"
                                    value={idx}
                                    checked={selectedOption === idx}
                                    style={{ display: 'none' }}
                                    onChange={() => handleOptionSelect(idx)}
                                />
                                {/* Custom ETS Oval Radio */}
                                <div style={{
                                    width: '36px',
                                    height: '20px',
                                    borderRadius: '50%',
                                    border: '1px solid #767676',
                                    backgroundColor: selectedOption === idx ? '#000000' : '#FFFFFF',
                                    marginRight: '20px',
                                    flexShrink: 0
                                }} />
                                {/* Option Text */}
                                <span style={{
                                    fontSize: '18px',
                                    color: '#5E6A75',
                                    lineHeight: 1.5
                                }}>
                                    {opt}
                                </span>
                            </label>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};
