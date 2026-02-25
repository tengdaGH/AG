'use client';

import React, { useRef, useEffect, useState } from 'react';

/**
 * Expected stimulus syntax: 
 * "This is an example text where a {word_id:5} is missing."
 */
interface ClozeParagraphProps {
    stimulusText: string;
    onWordComplete: (wordId: string, value: string) => void;
}

// Sub-component that breaks the input into perfectly isolated HTML box slots
const ClozeSlotInput = ({ wordId, length, onWordComplete }: { wordId: string, length: number, onWordComplete: (id: string, val: string) => void }) => {
    const [val, setVal] = useState('');
    const [isFocused, setIsFocused] = useState(false);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const newVal = e.target.value.replace(/[^a-zA-Z]/g, '');
        setVal(newVal);
        onWordComplete(wordId, newVal);
    };

    return (
        <span
            style={{
                position: 'relative',
                display: 'inline-block',
                margin: '0 4px',
                verticalAlign: 'middle',
                lineHeight: 1
            }}
        >
            {/* Visual Slots Container */}
            <span style={{ display: 'inline-flex', gap: '2px' }}>
                {Array.from({ length }).map((_, i) => {
                    const char = val[i] || '\u00A0'; // Force baseline calculation with non-breaking space
                    const isCurrentSlot = isFocused && val.length === i;
                    const isAtEnd = isFocused && i === length - 1 && val.length === length;

                    return (
                        <span
                            key={i}
                            style={{
                                width: '16px',
                                height: '24px',
                                display: 'inline-flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                borderBottom: isFocused ? '2px solid #005587' : '2px solid #212121',
                                backgroundColor: '#E5E7EB',
                                position: 'relative',
                                fontFamily: 'inherit',
                                fontSize: '18px',
                                fontWeight: 'bold',
                                color: '#005587',
                                lineHeight: 1
                            }}
                        >
                            {char}

                            {/* Simulated Hardware Caret */}
                            {isCurrentSlot && (
                                <span
                                    style={{
                                        position: 'absolute',
                                        left: '50%',
                                        transform: 'translateX(-50%)',
                                        width: '2px',
                                        height: '18px',
                                        backgroundColor: '#212121',
                                        animation: 'ets-blink 1s step-end infinite'
                                    }}
                                />
                            )}
                            {isAtEnd && (
                                <span
                                    style={{
                                        position: 'absolute',
                                        right: '0px',
                                        width: '2px',
                                        height: '18px',
                                        backgroundColor: '#212121',
                                        animation: 'ets-blink 1s step-end infinite'
                                    }}
                                />
                            )}
                        </span>
                    );
                })}
            </span>

            {/* Hidden Input Capture Overlay */}
            <input
                data-word-id={wordId}
                maxLength={length}
                className="ets-cloze-box"
                autoComplete="off"
                autoCorrect="off"
                autoCapitalize="off"
                spellCheck={false}
                data-gramm="false"
                value={val}
                onChange={handleChange}
                onFocus={() => setIsFocused(true)}
                onBlur={() => setIsFocused(false)}
                style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%',
                    opacity: 0,
                    cursor: 'text',
                    padding: 0,
                    margin: 0,
                    border: 'none',
                    zIndex: 1
                }}
            />
        </span>
    );
};

export const ClozeParagraph: React.FC<ClozeParagraphProps> = ({
    stimulusText,
    onWordComplete
}) => {
    const containerRef = useRef<HTMLDivElement>(null);

    const parsedContent = React.useMemo(() => {
        const regex = /\{([^:]+):([0-9]+)\}/g;
        const parts = [];
        let lastIndex = 0;
        let match;

        while ((match = regex.exec(stimulusText)) !== null) {
            if (match.index > lastIndex) {
                parts.push(<span key={`text-${lastIndex}`}>{stimulusText.slice(lastIndex, match.index)}</span>);
            }

            const wordId = match[1];
            const length = parseInt(match[2], 10);

            parts.push(
                <ClozeSlotInput
                    key={`cloze-${wordId}`}
                    wordId={wordId}
                    length={length}
                    onWordComplete={onWordComplete}
                />
            );

            lastIndex = regex.lastIndex;
        }

        if (lastIndex < stimulusText.length) {
            parts.push(<span key={`text-end`}>{stimulusText.slice(lastIndex)}</span>);
        }

        return parts;
    }, [stimulusText, onWordComplete]);

    // The Auto-Advance Physics Protocol
    useEffect(() => {
        if (!containerRef.current) return;

        const inputs = Array.from(containerRef.current.querySelectorAll('.ets-cloze-box')) as HTMLInputElement[];

        const handleKeyDown = (e: KeyboardEvent) => {
            const target = e.target as HTMLInputElement;
            const currentIndex = inputs.indexOf(target);

            // Intercept non-alphabetical
            if (e.key.length === 1 && !/^[a-zA-Z]$/.test(e.key)) {
                e.preventDefault();
                return;
            }

            // Backspace regression logic mapped to the React controlled input
            if (e.key === 'Backspace' && target.value.length === 0 && currentIndex > 0) {
                e.preventDefault();
                const prevInput = inputs[currentIndex - 1];
                prevInput.focus();

                const prevVal = prevInput.value;
                if (prevVal.length > 0) {
                    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value")?.set;
                    nativeInputValueSetter?.call(prevInput, prevVal.slice(0, -1));
                    prevInput.dispatchEvent(new Event('input', { bubbles: true }));
                }
            }
        };

        const handleKeyUp = (e: KeyboardEvent) => {
            const target = e.target as HTMLInputElement;
            const currentIndex = inputs.indexOf(target);

            // Auto-advance logic
            if (target.value.length >= target.maxLength && currentIndex < inputs.length - 1) {
                inputs[currentIndex + 1].focus();
            }
        };

        inputs.forEach(input => {
            input.addEventListener('keydown', handleKeyDown);
            input.addEventListener('keyup', handleKeyUp);
        });

        return () => {
            inputs.forEach(input => {
                input.removeEventListener('keydown', handleKeyDown);
                input.removeEventListener('keyup', handleKeyUp);
            });
        };
    }, [parsedContent]);

    return (
        <div
            ref={containerRef}
            style={{
                fontFamily: 'Times New Roman, Times, serif',
                fontSize: '18px',
                lineHeight: 1.8,
                color: '#212121',
                padding: '20px',
                textAlign: 'left',
                display: 'flex',
                flexDirection: 'column',
                height: '100%',
                backgroundColor: '#FFFFFF'
            }}
        >
            <style>{`
                @keyframes ets-blink {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0; }
                }
            `}</style>

            {/* Prominent ETS Instructional Header */}
            <div style={{ textAlign: 'center', width: '100%', marginTop: '40px', marginBottom: '60px' }}>
                <div style={{
                    display: 'inline-block',
                    padding: '0 40px'
                }}>
                    <h2 style={{
                        margin: 0,
                        color: '#008080', // Teal
                        fontSize: '20px',
                        fontWeight: 'bold',
                        fontFamily: 'Times New Roman, Times, serif'
                    }}>
                        Fill in the missing letters in the paragraph.
                    </h2>
                </div>
            </div>

            {/* Vertically Centered Stimulus Paragraph */}
            <div style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '0 40px'
            }}>
                <div style={{ maxWidth: '850px', width: '100%' }}>
                    {parsedContent}
                </div>
            </div>
        </div>
    );
};
