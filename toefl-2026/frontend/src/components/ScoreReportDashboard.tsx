'use client';

import React from 'react';

interface ScoreData {
    band: number;
    cefr: string;
    legacyRange: string;
}

interface MyBestScore {
    band: number;
    date: string;
}

interface ScoreReportDashboardProps {
    candidateName: string;
    etsId: string;
    testDate: string;
    photoUrl?: string; // Optional ENTRUST photo
    qrCodeUrl?: string;
    scores: {
        reading: ScoreData;
        listening: ScoreData;
        speaking: ScoreData;
        writing: ScoreData;
        total: ScoreData;
    };
    myBest: {
        reading: MyBestScore;
        listening: MyBestScore;
        speaking: MyBestScore;
        writing: MyBestScore;
        total: number;
    };
    feedback: {
        reading: string;
        writing: string;
    };
}

export const ScoreReportDashboard: React.FC<ScoreReportDashboardProps> = ({
    candidateName,
    etsId,
    testDate,
    photoUrl,
    qrCodeUrl,
    scores,
    myBest,
    feedback,
}) => {
    // Utility to render the horizontal progress bar relative to the max 6.0 scale
    const renderProgressBar = (band: number, isTotal = false) => {
        const percentage = (band / 6.0) * 100;
        const color = isTotal ? '#D32F2F' : '#005587';
        return (
            <div style={{ width: '100%', height: '12px', backgroundColor: '#E5E7EB', borderRadius: '6px', overflow: 'hidden', marginTop: '8px' }}>
                <div style={{ height: '100%', width: `${percentage}%`, backgroundColor: color, transition: 'width 0.5s ease-out' }} />
            </div>
        );
    };

    return (
        <div style={{
            maxWidth: '1000px', margin: '40px auto', padding: '0 20px',
            fontFamily: 'Arial, Helvetica, sans-serif', color: '#212121'
        }}>

            {/* Zone 1: Header & Identity */}
            <div style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                borderBottom: '2px solid #005587', paddingBottom: '20px', marginBottom: '30px'
            }}>
                <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
                    {photoUrl ? (
                        <div style={{ width: '100px', height: '130px', backgroundColor: '#F4F5F7', backgroundImage: `url(${photoUrl})`, backgroundSize: 'cover', backgroundPosition: 'center', border: '1px solid #D1D6E0' }} />
                    ) : (
                        <div style={{ width: '100px', height: '130px', backgroundColor: '#E5E7EB', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#9CA3AF', fontSize: '12px', border: '1px solid #D1D6E0' }}>No Photo</div>
                    )}
                    <div>
                        <h1 style={{ margin: '0 0 5px 0', fontSize: '28px', color: '#005587' }}>{candidateName}</h1>
                        <p style={{ margin: '0 0 5px 0', color: '#5E6A75', fontWeight: 'bold' }}>ETS ID: {etsId}</p>
                        <p style={{ margin: 0, color: '#5E6A75' }}>Test Date: {testDate}</p>
                    </div>
                </div>
                {qrCodeUrl && (
                    <div style={{ textAlign: 'center' }}>
                        <img src={qrCodeUrl} alt="Security QR Code" style={{ width: '100px', height: '100px' }} />
                        <p style={{ fontSize: '12px', color: '#9CA3AF', margin: '5px 0 0 0' }}>Official Verification</p>
                    </div>
                )}
            </div>

            {/* Zone 2: Dual-Score Matrix */}
            <h2 style={{ fontSize: '22px', borderBottom: '1px solid #D1D6E0', paddingBottom: '10px', marginBottom: '20px' }}>Your Scores</h2>

            <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '40px' }}>
                <thead>
                    <tr style={{ backgroundColor: '#F4F5F7', borderTop: '2px solid #212121', borderBottom: '2px solid #212121' }}>
                        <th style={{ padding: '15px', textAlign: 'left', width: '25%' }}>Skill</th>
                        <th style={{ padding: '15px', textAlign: 'left', width: '35%' }}>2026 Band Score (1.0-6.0)</th>
                        <th style={{ padding: '15px', textAlign: 'center', width: '20%' }}>CEFR Level</th>
                        <th style={{ padding: '15px', textAlign: 'center', width: '20%' }}>Legacy (0-30)</th>
                    </tr>
                </thead>
                <tbody>
                    {[
                        { name: 'Reading', data: scores.reading },
                        { name: 'Listening', data: scores.listening },
                        { name: 'Speaking', data: scores.speaking },
                        { name: 'Writing', data: scores.writing },
                    ].map((section, idx) => (
                        <tr key={idx} style={{ borderBottom: '1px solid #E5E7EB' }}>
                            <td style={{ padding: '15px', fontWeight: 'bold' }}>{section.name}</td>
                            <td style={{ padding: '15px' }}>
                                <span style={{ fontWeight: 'bold', fontSize: '18px', color: '#005587' }}>{section.data.band.toFixed(1)}</span>
                                {renderProgressBar(section.data.band)}
                            </td>
                            <td style={{ padding: '15px', textAlign: 'center', fontWeight: 'bold' }}>{section.data.cefr}</td>
                            <td style={{ padding: '15px', textAlign: 'center', color: '#5E6A75' }}>{section.data.legacyRange}</td>
                        </tr>
                    ))}

                    {/* Overall Score Row */}
                    <tr style={{ backgroundColor: '#F9FAFB', borderBottom: '2px solid #212121' }}>
                        <td style={{ padding: '15px', fontWeight: 'bold', fontSize: '18px' }}>OVERALL TOTAL</td>
                        <td style={{ padding: '15px' }}>
                            <span style={{ fontWeight: 'bold', fontSize: '24px', color: '#D32F2F' }}>{scores.total.band.toFixed(1)}</span>
                            {renderProgressBar(scores.total.band, true)}
                        </td>
                        <td style={{ padding: '15px', textAlign: 'center', fontWeight: 'bold', fontSize: '18px' }}>{scores.total.cefr}</td>
                        <td style={{ padding: '15px', textAlign: 'center', fontWeight: 'bold', color: '#5E6A75' }}>{scores.total.legacyRange} / 120</td>
                    </tr>
                </tbody>
            </table>

            <div style={{ display: 'flex', gap: '40px' }}>
                {/* Zone 3: MyBest Scores */}
                <div style={{ flex: 1 }}>
                    <h2 style={{ fontSize: '20px', borderBottom: '1px solid #D1D6E0', paddingBottom: '10px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                        MyBest® Scores <span style={{ fontSize: '12px', fontWeight: 'normal', backgroundColor: '#Eab308', color: '#FFF', padding: '2px 6px', borderRadius: '4px' }}>Superscore</span>
                    </h2>
                    <div style={{ border: '1px solid #D1D6E0', padding: '20px', borderRadius: '8px', backgroundColor: '#FDFDFD' }}>
                        <div style={{ textAlign: 'center', marginBottom: '20px' }}>
                            <div style={{ fontSize: '14px', color: '#5E6A75', fontWeight: 'bold' }}>Highest Overall Band</div>
                            <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#005587' }}>{myBest.total.toFixed(1)}</div>
                        </div>
                        {[
                            { name: 'Reading', data: myBest.reading },
                            { name: 'Listening', data: myBest.listening },
                            { name: 'Speaking', data: myBest.speaking },
                            { name: 'Writing', data: myBest.writing },
                        ].map((skill, idx) => (
                            <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: idx < 3 ? '1px solid #E5E7EB' : 'none' }}>
                                <span style={{ fontWeight: 'bold' }}>{skill.name}</span>
                                <div style={{ textAlign: 'right' }}>
                                    <span style={{ fontWeight: 'bold', color: '#005587', marginRight: '15px' }}>{skill.data.band.toFixed(1)}</span>
                                    <span style={{ fontSize: '12px', color: '#9CA3AF' }}>{skill.data.date}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Zone 4: Performance Feedback (2026 Specifics) */}
                <div style={{ flex: 1 }}>
                    <h2 style={{ fontSize: '20px', borderBottom: '1px solid #D1D6E0', paddingBottom: '10px', marginBottom: '20px' }}>Performance Feedback</h2>
                    <div style={{ backgroundColor: '#F4F5F7', padding: '20px', borderRadius: '8px' }}>
                        <h3 style={{ fontSize: '16px', color: '#212121', marginTop: 0 }}>Reading & Listening Analysis</h3>
                        <p style={{ fontSize: '14px', lineHeight: 1.6, color: '#5E6A75', marginBottom: '20px' }}>{feedback.reading}</p>

                        <h3 style={{ fontSize: '16px', color: '#212121' }}>Speaking & Writing Analysis</h3>
                        <p style={{ fontSize: '14px', lineHeight: 1.6, color: '#5E6A75', margin: 0 }}>{feedback.writing}</p>
                    </div>
                </div>
            </div>

            <div style={{ textAlign: 'center', marginTop: '50px', paddingTop: '20px', borderTop: '2px solid #D1D6E0' }}>
                <button style={{ backgroundColor: '#005587', color: '#FFFFFF', border: 'none', padding: '12px 30px', fontSize: '16px', fontWeight: 'bold', borderRadius: '4px', cursor: 'pointer' }}>
                    Download Official PDF Report
                </button>
            </div>
        </div>
    );
};
