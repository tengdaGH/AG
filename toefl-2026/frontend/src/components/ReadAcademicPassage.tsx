import React from 'react';

interface ReadAcademicPassageProps {
    title: string;
    content: string;
    headerText?: string;
    targetWord?: string;
    children: React.ReactNode; // The right-side questions
}

export const ReadAcademicPassage: React.FC<ReadAcademicPassageProps> = ({
    title,
    content,
    headerText = "Read an academic passage.",
    targetWord,
    children
}) => {
    return (
        <div style={{ display: 'flex', flexDirection: 'column', width: '100%', height: '100%', backgroundColor: '#FFFFFF', borderTop: '1px solid #767676' }}>

            {/* Split Screen Area */}
            <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
                {/* Left Pane: Stimulus Text */}
                <div
                    style={{
                        flex: '1 1 50%',
                        padding: '40px',
                        display: 'flex',
                        flexDirection: 'column',
                        overflowY: 'scroll', // Force scrollbar to be visible
                        scrollbarWidth: 'auto', // For Firefox
                        scrollbarColor: '#9CA3AF #F3F4F6' // thumb and track for Firefox
                    }}
                    className="ets-scrollbar" // Added generic class for potential global styling
                >
                    <style>{`
                        .ets-scrollbar::-webkit-scrollbar {
                            width: 12px;
                        }
                        .ets-scrollbar::-webkit-scrollbar-track {
                            background: #F3F4F6;
                            border-radius: 4px;
                        }
                        .ets-scrollbar::-webkit-scrollbar-thumb {
                            background-color: #9CA3AF;
                            border-radius: 4px;
                            border: 3px solid #F3F4F6;
                        }
                    `}</style>
                    <div style={{ maxWidth: '600px', margin: '0 auto', width: '100%' }}>
                        {title && (
                            <h2 style={{ fontSize: '24px', fontWeight: 'bold', textAlign: 'center', marginBottom: '24px', fontFamily: 'Arial, Helvetica, sans-serif' }}>
                                {title}
                            </h2>
                        )}
                        {content.split('\n').map((paragraph, index) => {
                            const cleanedParagraph = paragraph
                                .replace(/\(begin highlight\)/gi, '')
                                .replace(/\(end highlight\)/gi, '')
                                .replace(/\s*\([A-D]\)\s*/g, ' ')
                                .trim();
                            let pContent: React.ReactNode = cleanedParagraph;
                            if (targetWord) {
                                // Escape regex special characters from targetWord
                                const escapedWord = targetWord.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                                const regex = new RegExp(`\\b(${escapedWord})\\b`, 'i');
                                const parts = cleanedParagraph.split(regex);
                                pContent = parts.map((part, i) => {
                                    if (part.toLowerCase() === targetWord.toLowerCase()) {
                                        return <span key={i} style={{ backgroundColor: '#E2E8F0', fontWeight: 'bold', padding: '0 4px', borderRadius: '4px' }}>{part}</span>;
                                    }
                                    return part;
                                });
                            }
                            return (
                                <p key={index} style={{ fontSize: '18px', lineHeight: 1.8, color: '#000000', marginBottom: '16px', fontFamily: 'Times New Roman, Times, serif' }}>
                                    {pContent}
                                </p>
                            );
                        })}
                    </div>
                </div>

                {/* Right Pane: Questions */}
                <div
                    style={{
                        flex: '1 1 50%',
                        padding: '40px',
                        overflowY: 'auto'
                    }}
                >
                    {children}
                </div>
            </div>
        </div>
    );
};
