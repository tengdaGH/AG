'use client';

import React, { useEffect, useState, useRef } from 'react';
import styles from '../app/test-session/test-shell.module.css';
import { TestTimer } from './TestTimer';

interface TestShellProps {
    children: React.ReactNode;
    candidateName: string;
    etsId: string;
    sectionName: string;
    initialSeconds: number;
    onTimeUp: () => void;
    onNext: () => void;
    onBack: () => void;
    isNextDisabled?: boolean;
    isBackDisabled?: boolean;
}

export const TestShell: React.FC<TestShellProps> = ({
    children,
    candidateName,
    etsId,
    sectionName,
    initialSeconds,
    onTimeUp,
    onNext,
    onBack,
    isNextDisabled = false,
    isBackDisabled = false,
}) => {
    const [isFocused, setIsFocused] = useState(true);
    const [isFullscreen, setIsFullscreen] = useState(false);
    const shellRef = useRef<HTMLDivElement>(null);

    // Enter Fullscreen
    const enterFullscreen = async () => {
        if (shellRef.current && !document.fullscreenElement) {
            try {
                await shellRef.current.requestFullscreen();
            } catch (err) {
                console.error("Error attempting to enable fullscreen:", err);
            }
        }
    };

    // Event Listeners for Lockdown
    useEffect(() => {
        const handleContextMenu = (e: MouseEvent) => {
            e.preventDefault();
        };

        const handleKeyDown = (e: KeyboardEvent) => {
            // Trap Escape key
            if (e.key === 'Escape') {
                e.preventDefault();
            }

            // Trap Copy/Paste/Cut Shortcuts
            if ((e.ctrlKey || e.metaKey) && ['c', 'v', 'x'].includes(e.key.toLowerCase())) {
                e.preventDefault();
            }
        };

        const handleBlur = () => setIsFocused(false);
        const handleFocus = () => setIsFocused(true);

        const handleFullscreenChange = () => {
            setIsFullscreen(!!document.fullscreenElement);
            if (!document.fullscreenElement) {
                setIsFocused(false);
            }
        };

        document.addEventListener('contextmenu', handleContextMenu);
        document.addEventListener('keydown', handleKeyDown);
        window.addEventListener('blur', handleBlur);
        window.addEventListener('focus', handleFocus);
        document.addEventListener('fullscreenchange', handleFullscreenChange);

        return () => {
            document.removeEventListener('contextmenu', handleContextMenu);
            document.removeEventListener('keydown', handleKeyDown);
            window.removeEventListener('blur', handleBlur);
            window.removeEventListener('focus', handleFocus);
            document.removeEventListener('fullscreenchange', handleFullscreenChange);
        };
    }, []);

    return (
        <div className={styles.testShell} ref={shellRef}>
            {/* Security Warning Overlay */}
            {(!isFocused || !isFullscreen) && (
                <div className={styles.lockdownWarning}>
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginBottom: '20px' }}>
                        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                        <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                    </svg>
                    <p>SECURITY WARNING: Testing window has lost focus.</p>
                    <p style={{ fontSize: '16px', marginTop: '10px', color: '#FFFFFF' }}>Return to fullscreen to continue. Incident logged.</p>
                    <button
                        className={styles.etsButton}
                        style={{ marginTop: '30px' }}
                        onClick={() => {
                            enterFullscreen();
                            setIsFocused(true);
                        }}
                    >
                        Resume Test
                    </button>
                </div>
            )}

            {/* Top Header Bar */}
            <header className={styles.header}>
                <div className={styles.candidateInfo}>
                    {candidateName} | ETS ID: {etsId}
                </div>
                <div className={styles.sectionIndicator}>
                    {sectionName}
                </div>
                <div className={styles.timerContainer}>
                    <TestTimer initialSeconds={initialSeconds} onTimeUp={onTimeUp} />
                </div>
            </header>

            {/* Main Content Area */}
            <main className={styles.mainCanvas}>
                <div className={styles.contentArea}>
                    {children}
                </div>
            </main>

            {/* Bottom Footer Navigation */}
            <footer className={styles.footer}>
                <div className={styles.footerLeft}>
                    <button className={styles.etsButton} style={{ background: 'none', color: '#212121', border: '1px solid #D1D6E0' }}>
                        Volume
                    </button>
                    <button className={styles.etsTextButton}>
                        Help
                    </button>
                </div>

                <div className={styles.footerRight}>
                    <button
                        className={styles.etsButton}
                        onClick={onBack}
                        disabled={isBackDisabled}
                    >
                        Back
                    </button>
                    <button
                        className={styles.etsButton}
                        onClick={onNext}
                        disabled={isNextDisabled}
                    >
                        Next
                    </button>
                </div>
            </footer>
        </div>
    );
};
