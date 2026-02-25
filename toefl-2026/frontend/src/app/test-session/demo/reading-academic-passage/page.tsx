'use client';

import React, { useState } from 'react';
import { ReadAcademicPassage } from '../../../../components/ReadAcademicPassage';

const DEMO_ITEM = {
    title: "The Water Cycle",
    content: "The water cycle, also known as the hydrological cycle, describes the continuous movement of water on, above, and below the surface of the Earth. Water changes state between liquid, vapour, and ice as it moves through the cycle.\n\nEvaporation from oceans, lakes, and rivers adds water vapour to the atmosphere. Plants also release water vapour through a process called transpiration. When the water vapour rises and cools, it condenses to form clouds. Precipitation—rain, snow, sleet, or hail—returns water to the surface. Some of this water runs off into streams and rivers, eventually reaching the ocean. Another portion seeps into the ground and becomes groundwater, which may later emerge in springs or be taken up by plant roots.\n\nThe cycle has no real beginning or end, but scientists often start by describing the ocean, which holds about 97 percent of Earth's water. Solar energy drives evaporation, and gravity pulls precipitation downward. Human activities, such as irrigation and the building of reservoirs, can alter local water distribution, but the global cycle as a whole remains balanced. Understanding the water cycle is essential for managing freshwater resources and predicting the effects of climate change on rainfall and drought.",
    questions: [
        {
            text: "What is the main purpose of the passage?",
            options: [
                "To compare different types of precipitation",
                "To describe the continuous movement of water on Earth",
                "To explain how plants use groundwater",
                "To argue that human activities harm the water cycle"
            ]
        },
        {
            text: "According to the passage, what process do plants use to release water vapour into the atmosphere?",
            options: [
                "Evaporation",
                "Condensation",
                "Transpiration",
                "Precipitation"
            ]
        },
        {
            text: "According to the passage, where is most of Earth's water stored?",
            options: [
                "In the ocean",
                "In rivers and streams",
                "In the atmosphere as vapour",
                "In groundwater"
            ]
        }
    ]
};

export default function ReadingAcademicDemoPage() {
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [selectedOption, setSelectedOption] = useState<number | null>(null);

    const currentQuestion = DEMO_ITEM.questions[currentQuestionIndex];

    return (
        <div style={{ padding: '40px', maxWidth: '1200px', height: '80vh', margin: '0 auto', fontFamily: 'Arial, Helvetica, sans-serif' }}>
            <h1 style={{ color: '#005587', marginBottom: '20px' }}>Physics Sandbox: Read an Academic Passage</h1>
            <p style={{ color: '#5E6A75', marginBottom: '30px' }}>
                This verifies that the Academic Passage reading task mirrors the exact same ETS visual mechanics (split screen, flat radio buttons, teal headers) as the Daily Life reading task.
            </p>

            <div style={{ height: '600px', border: '1px solid #D1D6E0', borderRadius: '8px', overflow: 'hidden', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
                <ReadAcademicPassage
                    title={DEMO_ITEM.title}
                    content={DEMO_ITEM.content}
                    headerText="Read an academic passage."
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
                                {currentQuestionIndex < DEMO_ITEM.questions.length - 1 && (
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
                </ReadAcademicPassage>
            </div>
        </div>
    );
}
