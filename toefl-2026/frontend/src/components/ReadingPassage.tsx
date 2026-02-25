'use client';

import React from 'react';
import { Card, CardContent } from '@/components/Card';

interface Question {
    question_num: number;
    text: string;
    options: string[];
    correct_answer: number;
}

interface ReadingItemProps {
    type: string;
    title: string;
    text: string;
    questions?: Question[];
    currentQuestionIndex: number;
    onAnswerChange: (questionNum: number, answerIndex: number) => void;
    answers: Record<number, number>;
}

export const ReadingPassage: React.FC<ReadingItemProps> = ({
    type,
    title,
    text,
    questions = [],
    currentQuestionIndex,
    onAnswerChange,
    answers
}) => {
    const isCtest = type.includes('Complete');

    const renderCtestText = () => {
        return (
            <p style={{ fontSize: '1.125rem', lineHeight: 2, color: '#334155', whiteSpace: 'pre-wrap', fontFamily: 'Georgia, serif' }}>
                {text.split(/(_+)/).map((part, index) =>
                    part.match(/_+/) ? (
                        <span key={index} style={{
                            display: 'inline-block',
                            borderBottom: '2px solid #7c3aed',
                            minWidth: `${part.length * 10}px`,
                            padding: '0 4px',
                            margin: '0 2px',
                            color: '#7c3aed',
                            fontWeight: 600,
                        }}>{part}</span>
                    ) : <span key={index}>{part}</span>
                )}
            </p>
        );
    };

    const renderStandardText = () => {
        return (
            <div style={{ fontSize: '1.125rem', lineHeight: 1.8, color: '#334155', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {text.split('\n').map((para, i) => (
                    <p key={i}>{para}</p>
                ))}
            </div>
        );
    };

    return (
        <Card style={{ flex: 1, height: 'calc(100vh - 8rem)', overflowY: 'auto' }}>
            <CardContent style={{ padding: '2rem' }}>
                <h2 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '1.5rem' }}>{title}</h2>
                {isCtest ? renderCtestText() : renderStandardText()}
            </CardContent>
        </Card>
    );
};
