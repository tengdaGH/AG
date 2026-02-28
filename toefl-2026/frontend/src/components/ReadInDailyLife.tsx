'use client';

import React, { useState } from 'react';

interface ReadInDailyLifeProps {
    imageUrl?: string;
    stimulusText?: string;
    contentObj?: any;
    altText?: string;
    headerText?: string;
    stimulusType?: 'notice' | 'social_media' | 'email' | 'text_messages' | 'menu' | 'schedule' | 'default';
    children: React.ReactNode; // The right-side questions
}

export const ReadInDailyLife: React.FC<ReadInDailyLifeProps> = ({
    imageUrl,
    stimulusText,
    contentObj,
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

    const renderContent = () => {
        if (contentObj?.type === 'text_messages' && Array.isArray(contentObj.messages)) {
            const firstSender = contentObj.messages[0]?.sender;
            return (
                <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px', fontFamily: 'system-ui, -apple-system, sans-serif', width: '100%', overflowY: 'auto' }}>
                    {contentObj.messages.map((m: any, i: number) => {
                        const isSelf = m.sender === firstSender;
                        return (
                            <div key={i} style={{ alignSelf: isSelf ? 'flex-end' : 'flex-start', maxWidth: '85%', display: 'flex', flexDirection: 'column' }}>
                                <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px', textAlign: isSelf ? 'right' : 'left', alignSelf: isSelf ? 'flex-end' : 'flex-start', padding: '0 4px' }}>{m.sender}</div>
                                <div style={{
                                    background: isSelf ? '#DCF8C6' : '#E8E8E8',
                                    padding: '12px 16px',
                                    borderRadius: '18px',
                                    borderBottomRightRadius: isSelf ? '4px' : '18px',
                                    borderBottomLeftRadius: isSelf ? '18px' : '4px',
                                    fontSize: '15px',
                                    color: '#000',
                                    lineHeight: 1.4
                                }}>
                                    {m.text}
                                </div>
                            </div>
                        );
                    })}
                </div>
            );
        }

        if (contentObj?.type === 'email') {
            return (
                <div style={{ padding: '24px', fontFamily: 'system-ui, -apple-system, sans-serif', width: '100%', overflowY: 'auto' }}>
                    <div style={{ borderBottom: '1px solid #ddd', paddingBottom: '16px', marginBottom: '20px', fontSize: '15px' }}>
                        <div style={{ display: 'grid', gridTemplateColumns: 'max-content 1fr', rowGap: '6px', columnGap: '12px' }}>
                            <span style={{ color: '#666', fontWeight: 600, textAlign: 'right' }}>From:</span>
                            <span>{contentObj.from}</span>

                            <span style={{ color: '#666', fontWeight: 600, textAlign: 'right' }}>To:</span>
                            <span>{contentObj.to}</span>

                            <span style={{ color: '#666', fontWeight: 600, textAlign: 'right' }}>Date:</span>
                            <span>{contentObj.date}</span>

                            <span style={{ color: '#666', fontWeight: 600, textAlign: 'right' }}>Subject:</span>
                            <span style={{ fontWeight: 600 }}>{contentObj.subject}</span>
                        </div>
                    </div>
                    <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6, fontSize: '16px' }}>{contentObj.text || stimulusText}</div>
                </div>
            );
        }

        if (contentObj?.type === 'social_media') {
            return (
                <div style={{ padding: '24px', fontFamily: 'system-ui, -apple-system, sans-serif', width: '100%', overflowY: 'auto' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
                        <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: '#1A7A85', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: '20px' }}>
                            {contentObj.author ? contentObj.author.charAt(0).toUpperCase() : 'U'}
                        </div>
                        <div>
                            <div style={{ fontWeight: 600, fontSize: '16px' }}>{contentObj.author || 'User'}</div>
                            <div style={{ color: '#666', fontSize: '13px', marginTop: '2px' }}>{contentObj.date || 'Just now'}</div>
                        </div>
                    </div>
                    <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6, fontSize: '16px' }}>{contentObj.text || stimulusText}</div>
                </div>
            );
        }

        return (
            <div style={{
                width: '100%',
                height: '100%',
                overflowY: 'auto',
                fontSize: '16px',
                lineHeight: 1.6,
                textAlign: 'left',
                fontFamily: "'Times New Roman', Times, serif",
                whiteSpace: 'pre-wrap',
                color: '#333',
                padding: '24px'
            }}>
                {headerText && (
                    <h2 style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '16px', fontFamily: 'Arial, Helvetica, sans-serif', color: '#000' }}>
                        {headerText}
                    </h2>
                )}
                {contentObj?.text || stimulusText}
            </div>
        );
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', width: '100%', height: '100%', backgroundColor: '#FFFFFF', borderTop: '1px solid #767676' }}>

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
                                justifyContent: 'center',
                                padding: stimulusText ? '20px' : '0'
                            }}>
                                {imageUrl ? (
                                    <img
                                        src={imageUrl}
                                        alt={altText}
                                        draggable="false"
                                        style={{
                                            maxWidth: '100%',
                                            maxHeight: '100%',
                                            objectFit: 'contain',
                                            transform: isZoomed ? 'scale(2.5)' : 'scale(1)',
                                            transformOrigin: isZoomed ? `${mousePos.x}% ${mousePos.y}%` : 'center center',
                                            transition: isZoomed ? 'none' : 'transform 0.2s ease-out'
                                        }}
                                    />
                                ) : (
                                    renderContent()
                                )}
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
