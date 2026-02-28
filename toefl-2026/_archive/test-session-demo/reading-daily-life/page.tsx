'use client';

import React, { useState } from 'react';
import { ReadInDailyLife } from '../../../../components/ReadInDailyLife';

const DEMO_ITEMS = {
    notice: {
        title: "Scheduled water maintenance",
        text: "Dear residents,\n\nPlease be informed that our water supply will be temporarily shut off on Tuesday, 14 March, between 9:00 AM and 12:00 noon. This is necessary for repairs to the main pipeline in the basement.\n\nWe advise you to store some water in advance for drinking and basic use. The lift will continue to operate as usual. We apologise for any inconvenience and will complete the work as quickly as possible.",
        questions: [
            {
                text: "What is the main purpose of this email?",
                options: [
                    "To announce a new building management team",
                    "To inform residents about a temporary water shut-off for repairs",
                    "To remind residents to pay their water bills",
                    "To invite residents to a meeting about the building"
                ]
            },
            {
                text: "What should residents do before Tuesday?",
                options: [
                    "Leave the building during the maintenance",
                    "Contact the lift company",
                    "Store some water for drinking and basic use",
                    "Pay an extra fee for the repairs"
                ]
            }
        ]
    },
    social_media: {
        title: "Spring Clean-Up",
        text: "Join us this Saturday for our Spring Clean-Up! We'll meet at the main gate at 9:00 AM. We'll provide gloves and bags – just bring yourself and some water. All ages welcome. After the clean-up we'll have free tea and biscuits. No need to sign up in advance; just turn up. Let's make our neighbourhood greener! #GreenfieldCleanUp #Community",
        questions: [
            {
                text: "What is the main purpose of this post?",
                options: [
                    "To sell gloves and bags",
                    "To announce a new café at the community centre",
                    "To invite people to a community clean-up event",
                    "To ask for donations"
                ]
            },
            {
                text: "What do participants need to bring?",
                options: [
                    "Gloves and bags",
                    "Tea and biscuits",
                    "A sign-up form",
                    "Themselves and some water"
                ]
            }
        ]
    }
};

const getSvgImage = (title: string, text: string) => {
    const rawSvg = `
        <svg xmlns="http://www.w3.org/2000/svg" width="450" height="600">
            <foreignObject width="100%" height="100%">
                <div xmlns="http://www.w3.org/1999/xhtml" style="padding: 24px; font-family: Arial, Helvetica, sans-serif; font-size: 18px; line-height: 1.6; color: #1F2937; background-color: #FFFFFF; width: 100%; height: 100%; box-sizing: border-box;">
                    <h2 style="font-size: 22px; color: #111827; margin-top: 0; margin-bottom: 20px; border-bottom: 1px solid #E5E7EB; padding-bottom: 12px;">${title}</h2>
                    <p style="white-space: pre-wrap; margin: 0;">${text}</p>
                </div>
            </foreignObject>
        </svg>
    `;
    return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(rawSvg)}`;
};

export default function ReadingDailyLifeTweakPage() {
    const [currentType, setCurrentType] = useState<'notice' | 'social_media'>('notice');
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [selectedOption, setSelectedOption] = useState<number | null>(null);

    const currentItem = DEMO_ITEMS[currentType];
    const currentQuestion = currentItem.questions[currentQuestionIndex];
    const stimulusImageUrl = getSvgImage(currentItem.title, currentItem.text);

    const handleToggle = () => {
        setCurrentType(currentType === 'notice' ? 'social_media' : 'notice');
        setCurrentQuestionIndex(0); // Reset to first question on item switch
        setSelectedOption(null);
    };

    return (
        <div style={{ padding: '40px', maxWidth: '1200px', height: '80vh', margin: '0 auto', fontFamily: 'Arial, Helvetica, sans-serif' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h1 style={{ color: '#005587', margin: 0 }}>Physics Sandbox: Read in Daily Life</h1>
                <button
                    onClick={handleToggle}
                    style={{ padding: '8px 16px', backgroundColor: '#005587', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                >
                    Toggle Item Type: {currentType === 'notice' ? 'Notice (Paper)' : 'Social Media (Tablet)'}
                </button>
            </div>

            <p style={{ color: '#5E6A75', marginBottom: '30px' }}>
                This is an isolated sandbox to test the exactlyETS 50/50 split-screen interaction physics for the Reading section.<br />
                Try hovering over the image on the left to trigger the magnification (zoom) effect and pan around.
            </p>

            <div style={{ height: '600px', border: '1px solid #D1D6E0', borderRadius: '8px', overflow: 'hidden', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
                <ReadInDailyLife
                    imageUrl={stimulusImageUrl}
                    altText="Demo Reading Stimulus"
                    stimulusType={currentType}
                >
                    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                        <h2 style={{ fontSize: '20px', color: '#000000', marginBottom: '24px', fontFamily: 'Times New Roman, Times, serif', fontWeight: 'normal' }}>
                            {currentQuestionIndex + 1}. {currentQuestion.text}
                        </h2>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                            {currentQuestion.options.map((opt, i) => (
                                <label
                                    key={i}
                                    style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        padding: '12px 0',
                                        cursor: 'pointer',
                                    }}
                                >
                                    <input
                                        type="radio"
                                        name={`demo_q${currentQuestionIndex}`}
                                        style={{ display: 'none' }}
                                        checked={selectedOption === i}
                                        onChange={() => setSelectedOption(i)}
                                    />
                                    <div style={{
                                        width: '36px',
                                        height: '20px',
                                        borderRadius: '50%',
                                        border: '1px solid #000000',
                                        backgroundColor: selectedOption === i ? '#000000' : '#FFFFFF',
                                        marginRight: '16px',
                                        flexShrink: 0
                                    }} />
                                    <span style={{ fontSize: '18px', color: '#000000', fontFamily: 'Times New Roman, Times, serif' }}>{opt}</span>
                                </label>
                            ))}
                        </div>

                        {/* Local Navigation Component */}
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 'auto', paddingTop: '40px' }}>
                            <div>
                                {currentQuestionIndex > 0 && (
                                    <button
                                        onClick={() => { setCurrentQuestionIndex(prev => prev - 1); setSelectedOption(null); }}
                                        style={{ padding: '10px 24px', backgroundColor: '#FFFFFF', color: '#005587', border: '1px solid #005587', borderRadius: '24px', cursor: 'pointer', fontWeight: 'bold' }}
                                    >
                                        &larr; Back
                                    </button>
                                )}
                            </div>
                            <div>
                                {currentQuestionIndex < currentItem.questions.length - 1 && (
                                    <button
                                        onClick={() => { setCurrentQuestionIndex(prev => prev + 1); setSelectedOption(null); }}
                                        style={{ padding: '10px 24px', backgroundColor: '#005587', color: 'white', border: 'none', borderRadius: '24px', cursor: 'pointer', fontWeight: 'bold' }}
                                    >
                                        Next &rarr;
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                </ReadInDailyLife>
            </div>
        </div>
    );
}
