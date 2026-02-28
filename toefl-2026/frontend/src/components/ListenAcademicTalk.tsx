'use client';

import React, { useState, useEffect, useRef } from 'react';
import { CustomAudioPlayer } from './CustomAudioPlayer';

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
    const timerRef = useRef<NodeJS.Timeout | null>(null);

    // Reset state when the component receives a new question/audio
    useEffect(() => {
        setAudioFinished(false);
        setOptionsVisible(false);
        setSelectedOption(null);
        if (timerRef.current) clearTimeout(timerRef.current);
    }, [audioUrl, questionText]);

    useEffect(() => {
        return () => {
            if (timerRef.current) clearTimeout(timerRef.current);
        };
    }, []);

    const handleAudioEnded = () => {
        setAudioFinished(true);
        timerRef.current = setTimeout(() => {
            setOptionsVisible(true);
        }, 200);
    };

    const handleOptionSelect = (idx: number) => {
        setSelectedOption(idx);
        onOptionSelect(idx);
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', width: '100%', height: '100%', backgroundColor: '#FFFFFF', borderTop: '1px solid #767676', fontFamily: 'Times New Roman, Times, serif', alignItems: 'center', justifyContent: 'center', padding: '40px' }}>

            {!audioFinished ? (
                /* Phase 1: Listening (Audio playing, no questions) */
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '30px', maxWidth: '600px', width: '100%', animation: 'fadeIn 0.5s ease' }}>
                    {speakerImageUrl && (
                        <img
                            src={speakerImageUrl}
                            alt="Educator giving academic talk"
                            style={{ width: '100%', maxWidth: '350px', height: 'auto', objectFit: 'contain' }}
                        />
                    )}
                    <div style={{ width: '100%' }}>
                        <CustomAudioPlayer src={audioUrl} onEnded={handleAudioEnded} />
                    </div>
                    <p style={{ color: '#767676', fontSize: '15px', marginTop: '10px' }}>
                        Listen to the talk, then answer the question.
                    </p>
                </div>
            ) : (
                /* Phase 2: Answering (Question and options appear, image disappears) */
                <div style={{
                    opacity: optionsVisible ? 1 : 0,
                    pointerEvents: optionsVisible ? 'auto' : 'none',
                    transition: 'opacity 0.4s ease',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '30px',
                    maxWidth: '800px',
                    width: '100%',
                    justifyContent: 'flex-start',
                    alignItems: 'flex-start',
                    padding: '20px 40px'
                }}>
                    {/* Visible Question Text directly above options */}
                    <h3 style={{ fontSize: '20px', color: '#212121', marginBottom: '10px', fontWeight: 600, lineHeight: 1.4, fontFamily: 'Arial, Helvetica, sans-serif' }}>
                        {questionText}
                    </h3>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', width: '100%' }}>
                        {options.map((opt, idx) => (
                            <label
                                key={idx}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    cursor: 'pointer',
                                    padding: '8px 0'
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
                                    height: '22px',
                                    borderRadius: '50%',
                                    border: '1px solid #767676',
                                    backgroundColor: selectedOption === idx ? '#000000' : '#FFFFFF',
                                    marginRight: '20px',
                                    flexShrink: 0,
                                    transition: 'background-color 0.1s'
                                }} />
                                {/* Option Text */}
                                <span style={{
                                    fontSize: '18px',
                                    color: '#212121',
                                    lineHeight: 1.5,
                                }}>
                                    {opt}
                                </span>
                            </label>
                        ))}
                    </div>
                </div>
            )}
            <style>{`
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
            `}</style>
        </div>
    );
};
