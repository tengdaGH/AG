'use client';

import React, { useState } from 'react';

interface ReadInDailyLifeProps {
    imageUrl: string;
    altText?: string;
    headerText?: string;
    stimulusType?: 'notice' | 'social_media' | 'email' | 'text_messages' | 'menu' | 'schedule' | 'default';
    children: React.ReactNode; // The right-side questions
}

export const ReadInDailyLife: React.FC<ReadInDailyLifeProps> = ({
    imageUrl,
    altText = "Reading Stimulus",
    headerText = "Read a notice.",
    stimulusType = 'default',
    children
}) => {
    const [isZoomed, setIsZoomed] = useState(false);
    const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

    const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
        if (!isZoomed) return;
        const rect = e.currentTarget.getBoundingClientRect();
        // Calculate percentages for transform-origin
        const x = ((e.clientX - rect.left) / rect.width) * 100;
        const y = ((e.clientY - rect.top) / rect.height) * 100;
        setMousePos({ x, y });
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', width: '100%', height: '100%', backgroundColor: '#FFFFFF', border: '1px solid #767676' }}>
            {/* Header Area */}
            <div style={{ width: '100%', padding: '24px 0', borderBottom: '1px solid #767676', textAlign: 'center' }}>
                <h2 style={{ margin: 0, color: '#1A7A85', fontSize: '26px', fontWeight: 'bold', fontFamily: 'Arial, Helvetica, sans-serif' }}>
                    {headerText}
                </h2>
            </div>

            {/* Split Screen Area */}
            <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
                {/* Left Pane: Stimulus */}
                <div
                    style={{
                        flex: '1 1 50%',
                        padding: '40px',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        overflow: 'hidden' // Important for the zoom masking
                    }}
                >
                    <div
                        style={{
                            position: 'relative',
                            width: '100%',
                            height: '100%',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            cursor: isZoomed ? 'zoom-out' : 'zoom-in',
                            overflow: 'hidden'
                        }}
                        onClick={() => setIsZoomed(!isZoomed)}
                        onMouseMove={handleMouseMove}
                        onMouseLeave={() => setIsZoomed(false)}
                    >
                        {/* Conditional Device Frame Wrapper */}
                        <div style={{
                            position: 'relative',
                            width: stimulusType === 'social_media' || stimulusType === 'text_messages' ? '80%' : '90%',
                            height: stimulusType === 'social_media' || stimulusType === 'text_messages' ? '85%' : '90%',
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            // Tablet Frame styles
                            ...(stimulusType === 'social_media' || stimulusType === 'text_messages' ? {
                                backgroundColor: '#1C696B', // Tablet bezel color from ETS screenshot
                                borderRadius: '24px',
                                border: '6px solid #B0BEC5', // Outer casing
                                padding: '30px 10px 10px 10px',
                                boxShadow: '0 10px 25px rgba(0,0,0,0.15)',
                            } : {}),
                            // Paper/Notice Frame Styles
                            ...(stimulusType === 'notice' || stimulusType === 'email' || stimulusType === 'menu' || stimulusType === 'schedule' ? {
                                backgroundColor: '#FFFFFF',
                                border: '1px solid #767676',
                                padding: '2px', // Thin double border effect
                                boxShadow: '2px 2px 8px rgba(0,0,0,0.1)',
                            } : {})
                        }}>
                            {/* Inner white bezel for notice, or screen for tablet */}
                            <div style={{
                                width: '100%',
                                height: '100%',
                                backgroundColor: '#FFFFFF',
                                border: stimulusType === 'notice' || stimulusType === 'email' || stimulusType === 'menu' || stimulusType === 'schedule' ? '1px solid #767676' : 'none',
                                borderRadius: stimulusType === 'social_media' || stimulusType === 'text_messages' ? '12px 12px 4px 4px' : '0',
                                overflow: 'hidden',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center'
                            }}>
                                <img
                                    src={imageUrl}
                                    alt={altText}
                                    draggable="false" // Block desktop drag
                                    style={{
                                        maxWidth: '100%',
                                        maxHeight: '100%',
                                        objectFit: 'contain',
                                        transform: isZoomed ? 'scale(2.5)' : 'scale(1)',
                                        transformOrigin: isZoomed ? `${mousePos.x}% ${mousePos.y}%` : 'center center',
                                        transition: isZoomed ? 'none' : 'transform 0.2s ease-out'
                                    }}
                                />
                            </div>
                        </div>
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
