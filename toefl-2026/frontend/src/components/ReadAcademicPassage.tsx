import React from 'react';

interface ReadAcademicPassageProps {
    title: string;
    content: string;
    headerText?: string;
    children: React.ReactNode; // The right-side questions
}

export const ReadAcademicPassage: React.FC<ReadAcademicPassageProps> = ({
    title,
    content,
    headerText = "Read an academic passage.",
    children
}) => {
    return (
        <div style={{ display: 'flex', flexDirection: 'column', width: '100%', height: '100%', backgroundColor: '#FFFFFF', border: '1px solid #767676' }}>
            {/* Header Area */}
            <div style={{ width: '100%', padding: '24px 0', borderBottom: '1px solid #767676', textAlign: 'center' }}>
                <h2 style={{ margin: 0, color: '#1A7A85', fontSize: '26px', fontWeight: 'bold', fontFamily: 'Arial, Helvetica, sans-serif' }}>
                    {title}
                </h2>
            </div>

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
                        {content.split('\n').map((paragraph, index) => (
                            <p key={index} style={{ fontSize: '18px', lineHeight: 1.8, color: '#000000', marginBottom: '16px', fontFamily: 'Times New Roman, Times, serif' }}>
                                {paragraph}
                            </p>
                        ))}
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
