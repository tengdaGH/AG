'use client';

import React from 'react';

interface UnofficialScoreRevealProps {
    readingBand: number;
    readingLegacy: string;
    listeningBand: number;
    listeningLegacy: string;
    onContinue: () => void;
}

export const UnofficialScoreReveal: React.FC<UnofficialScoreRevealProps> = ({
    readingBand,
    readingLegacy,
    listeningBand,
    listeningLegacy,
    onContinue
}) => {
    return (
        <div style={{
            padding: '40px', maxWidth: '800px', margin: '40px auto',
            backgroundColor: '#FFFFFF', borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)', fontFamily: 'Arial, Helvetica, sans-serif'
        }}>
            <h1 style={{ color: '#005587', fontSize: '28px', marginBottom: '10px', textAlign: 'center' }}>
                Unofficial Scores
            </h1>
            <p style={{ color: '#5E6A75', textAlign: 'center', marginBottom: '40px' }}>
                These are unofficial scores for your Reading and Listening sections.
                Your official, finalized scores for all four sections will be available in your ETS Account within 72 hours.
            </p>

            <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '40px' }}>
                <thead>
                    <tr style={{ backgroundColor: '#F4F5F7', borderBottom: '2px solid #005587' }}>
                        <th style={{ padding: '15px', textAlign: 'left', color: '#212121' }}>Section</th>
                        <th style={{ padding: '15px', textAlign: 'center', color: '#212121' }}>2026 Band Score</th>
                        <th style={{ padding: '15px', textAlign: 'center', color: '#5E6A75', fontWeight: 'normal' }}>Legacy Equivalent</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style={{ borderBottom: '1px solid #D1D6E0' }}>
                        <td style={{ padding: '15px', fontWeight: 'bold', color: '#212121' }}>Reading</td>
                        <td style={{ padding: '15px', textAlign: 'center', fontSize: '20px', fontWeight: 'bold', color: '#005587' }}>
                            {readingBand.toFixed(1)}
                        </td>
                        <td style={{ padding: '15px', textAlign: 'center', color: '#5E6A75' }}>
                            {readingLegacy}
                        </td>
                    </tr>
                    <tr style={{ borderBottom: '1px solid #D1D6E0' }}>
                        <td style={{ padding: '15px', fontWeight: 'bold', color: '#212121' }}>Listening</td>
                        <td style={{ padding: '15px', textAlign: 'center', fontSize: '20px', fontWeight: 'bold', color: '#005587' }}>
                            {listeningBand.toFixed(1)}
                        </td>
                        <td style={{ padding: '15px', textAlign: 'center', color: '#5E6A75' }}>
                            {listeningLegacy}
                        </td>
                    </tr>
                </tbody>
            </table>

            <div style={{ textAlign: 'center' }}>
                <button
                    onClick={onContinue}
                    style={{
                        backgroundColor: '#005587', color: '#FFFFFF', border: 'none',
                        padding: '12px 30px', fontSize: '16px', fontWeight: 'bold',
                        borderRadius: '4px', cursor: 'pointer'
                    }}
                >
                    Continue to Dashboard
                </button>
            </div>
        </div>
    );
};
