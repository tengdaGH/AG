'use client';

import React, { useRef, useEffect } from 'react';

/**
 * Parses a paragraph with placeholders (e.g., "The quick {b}rown fox") 
 * and replaces them with strict inline cloze inputs for the 2026 update.
 */
interface CompleteTheWordsProps {
    stimulusHTML: string; // The paragraph containing {word_id:expected_length} markers
    onWordComplete: (wordId: string, value: string) => void;
}

export const CompleteTheWords: React.FC<CompleteTheWordsProps> = ({
    stimulusHTML,
    onWordComplete
}) => {
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!containerRef.current) return;

        const inputs = Array.from(containerRef.current.querySelectorAll('input.ets-inline-cloze')) as HTMLInputElement[];

        const handleKeyDown = (e: KeyboardEvent) => {
            const target = e.target as HTMLInputElement;
            const currentIndex = inputs.indexOf(target);

            // Backspace Handling: Jump backward if empty
            if (e.key === 'Backspace' && target.value.length === 0 && currentIndex > 0) {
                e.preventDefault();
                const prevInput = inputs[currentIndex - 1];
                prevInput.focus();
                // Strip the last character of the previous input
                prevInput.value = prevInput.value.slice(0, -1);
                // Fire update
                onWordComplete(prevInput.dataset.wordId || '', prevInput.value);
            }

            // Reject non-alphabetical characters
            if (e.key.length === 1 && !/^[a-zA-Z]$/.test(e.key)) {
                e.preventDefault();
            }
        };

        const handleInput = (e: Event) => {
            const target = e.target as HTMLInputElement;
            const maxLength = parseInt(target.getAttribute('maxlength') || '1', 10);
            const currentIndex = inputs.indexOf(target);

            // Extract the purely alphabetical strict value
            target.value = target.value.replace(/[^a-zA-Z]/g, '');

            onWordComplete(target.dataset.wordId || '', target.value);

            // Auto-advance logic
            if (target.value.length >= maxLength && currentIndex < inputs.length - 1) {
                target.blur();
                inputs[currentIndex + 1].focus();
            }
        };

        inputs.forEach(input => {
            input.addEventListener('keydown', handleKeyDown);
            input.addEventListener('input', handleInput);
        });

        return () => {
            inputs.forEach(input => {
                input.removeEventListener('keydown', handleKeyDown);
                input.removeEventListener('input', handleInput);
            });
        };
    }, [stimulusHTML, onWordComplete]);

    return (
        <div
            ref={containerRef}
            className="ets-reading-passage ets-cloze-task"
            style={{ fontSize: '16px', lineHeight: 1.65, color: '#212121', padding: '20px' }}
            dangerouslySetInnerHTML={{ __html: stimulusHTML }}
        />
    );
};
