'use client';

import React, { useState } from 'react';

interface ReportCancelModalProps {
    onReport: () => void;
    onCancel: () => void;
}

export const ReportCancelModal: React.FC<ReportCancelModalProps> = ({
    onReport,
    onCancel
}) => {
    const [isCanceling, setIsCanceling] = useState(false);
    const [cancelText, setCancelText] = useState('');

    const handleInitialCancelClick = () => {
        setIsCanceling(true);
    };

    const handleFinalCancelClick = () => {
        if (cancelText === 'CANCEL') {
            onCancel();
        }
    };

    return (
        <div style={{
            position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
            backgroundColor: '#F4F5F7', zIndex: 9999, display: 'flex',
            justifyContent: 'center', alignItems: 'center', fontFamily: 'Arial, Helvetica, sans-serif'
        }}>
            <div style={{
                backgroundColor: '#FFFFFF', padding: '40px', borderRadius: '8px',
                boxShadow: '0 4px 12px rgba(0,0,0,0.15)', maxWidth: '600px', width: '100%',
                textAlign: 'center'
            }}>
                <h1 style={{ color: '#212121', fontSize: '24px', marginBottom: '20px' }}>
                    End of Test: Report or Cancel Scores
                </h1>

                <p style={{ color: '#5E6A75', fontSize: '16px', lineHeight: 1.6, marginBottom: '30px', textAlign: 'left' }}>
                    Your test is complete. You must now choose whether to report or cancel your scores.
                    If you cancel, your scores will not be reported to you or any institutions, and no refund will be issued.
                </p>

                {!isCanceling ? (
                    <div style={{ display: 'flex', justifyContent: 'center', gap: '20px' }}>
                        <button
                            onClick={handleInitialCancelClick}
                            style={{
                                background: 'none', border: '1px solid #5E6A75', color: '#5E6A75',
                                padding: '12px 24px', fontSize: '16px', fontWeight: 'bold', borderRadius: '4px',
                                cursor: 'pointer'
                            }}>
                            Cancel Scores
                        </button>
                        <button
                            onClick={onReport}
                            style={{
                                backgroundColor: '#005587', border: 'none', color: '#FFFFFF',
                                padding: '12px 24px', fontSize: '16px', fontWeight: 'bold', borderRadius: '4px',
                                cursor: 'pointer'
                            }}>
                            Report Scores
                        </button>
                    </div>
                ) : (
                    <div style={{ borderTop: '1px solid #D1D6E0', paddingTop: '20px', textAlign: 'left' }}>
                        <p style={{ color: '#D32F2F', fontWeight: 'bold', marginBottom: '15px' }}>
                            WARNING: Score cancellation is permanent and cannot be reversed.
                        </p>
                        <p style={{ marginBottom: '10px' }}>Type <strong>CANCEL</strong> below to confirm:</p>
                        <input
                            type="text"
                            value={cancelText}
                            onChange={(e) => setCancelText(e.target.value)}
                            style={{
                                width: '100%', padding: '10px', fontSize: '16px',
                                border: '1px solid #D1D6E0', borderRadius: '4px', marginBottom: '20px'
                            }}
                            placeholder="CANCEL"
                        />
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '15px' }}>
                            <button
                                onClick={() => setIsCanceling(false)}
                                style={{
                                    background: 'none', border: 'none', color: '#005587',
                                    fontSize: '16px', fontWeight: 'bold', cursor: 'pointer'
                                }}>
                                Go Back
                            </button>
                            <button
                                onClick={handleFinalCancelClick}
                                disabled={cancelText !== 'CANCEL'}
                                style={{
                                    backgroundColor: cancelText === 'CANCEL' ? '#D32F2F' : '#E5E7EB',
                                    border: 'none', color: cancelText === 'CANCEL' ? '#FFFFFF' : '#9CA3AF',
                                    padding: '10px 20px', fontSize: '16px', fontWeight: 'bold', borderRadius: '4px',
                                    cursor: cancelText === 'CANCEL' ? 'pointer' : 'not-allowed'
                                }}>
                                Permanently Cancel
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
