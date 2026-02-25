'use client';

import React from 'react';
import { Card } from '@/components/Card';
import { Button } from '@/components/Button';

interface Question {
    question_num: number;
    text: string;
    options: string[];
    correct_answer: number;
}

interface ReadingQuestionProps {
    questions: Question[];
    currentQuestionIndex: number;
    onNext: () => void;
    onBack: () => void;
    onAnswerChange: (questionNum: number, answerIndex: number) => void;
    answers: Record<number, number>;
    totalQuestions: number;
    submitLabel: string;
    nextLabel: string;
    backLabel: string;
}

export const ReadingQuestion: React.FC<ReadingQuestionProps> = ({
    questions,
    currentQuestionIndex,
    onNext,
    onBack,
    onAnswerChange,
    answers,
    totalQuestions,
    submitLabel,
    nextLabel,
    backLabel
}) => {
    const currentQuestion = questions[currentQuestionIndex];

    if (!currentQuestion) return null;

    return (
        <Card style={{ flex: 1, height: 'calc(100vh - 8rem)', display: 'flex', flexDirection: 'column' }}>
            <div style={{ padding: '2rem', flex: 1, overflowY: 'auto' }}>
                <div style={{ marginBottom: '2rem' }}>
                    <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1rem' }}>
                        {currentQuestion.text.includes('_')
                            ? `Complete the word: ${currentQuestion.text}`
                            : currentQuestion.text}
                    </h3>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                        {currentQuestion.options.map((option, index) => (
                            <label
                                key={index}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '1rem',
                                    padding: '1rem',
                                    border: '1px solid #e2e8f0',
                                    borderRadius: '8px',
                                    cursor: 'pointer',
                                    transition: 'background-color 0.2s',
                                    backgroundColor: answers[currentQuestion.question_num] === index ? '#f1f5f9' : 'transparent',
                                    borderColor: answers[currentQuestion.question_num] === index ? '#334155' : '#e2e8f0'
                                }}
                            >
                                <input
                                    type="radio"
                                    name={`q${currentQuestion.question_num}`}
                                    checked={answers[currentQuestion.question_num] === index}
                                    onChange={() => onAnswerChange(currentQuestion.question_num, index)}
                                    style={{ width: '1.25rem', height: '1.25rem' }}
                                />
                                <span style={{ fontSize: '1.125rem' }}>{option}</span>
                            </label>
                        ))}
                    </div>
                </div>
            </div>

            {/* Footer Controls */}
            <div style={{ padding: '1.5rem', borderTop: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', backgroundColor: '#f8fafc' }}>
                <Button variant="secondary" disabled={currentQuestionIndex === 0} onClick={onBack}>
                    {backLabel}
                </Button>
                <Button onClick={onNext}>
                    {currentQuestionIndex === totalQuestions - 1 ? submitLabel : nextLabel}
                </Button>
            </div>
        </Card>
    );
};
