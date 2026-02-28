'use client';

import React, { useState, ChangeEvent } from 'react';

/**
 * Props for the C-Test Input component.
 * @property {string} prefix - The static text before the input (e.g., 'wat' for 'watches').
 * @property {number} targetLength - The exact number of characters expected in the answer.
 * @property {string} [initialValue] - Optional initial answered value.
 * @property {function} onChange - Callback triggered when the input value changes.
 */
interface CTestInputProps {
    prefix: string;
    targetLength: number;
    initialValue?: string;
    onChange?: (value: string) => void;
}

/**
 * CTestInput
 * 
 * An ETS-compliant C-Test/Cloze test input field.
 * Implements a single continuous HTML input overlaid with CSS dashed lines
 * to hint character count without breaking native browser text management
 * (like selection, caret positioning, and pasting).
 * 
 * Returns a clean string payload perfectly suited for backend evaluation.
 */
export const CTestInput: React.FC<CTestInputProps> = ({
    prefix,
    targetLength,
    initialValue = '',
    onChange
}) => {
    const [value, setValue] = useState<string>(initialValue);

    const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
        // Enforce maximum length at the React state level
        let newVal = e.target.value;
        if (newVal.length > targetLength) {
            newVal = newVal.slice(0, targetLength);
        }
        setValue(newVal);
        if (onChange) {
            onChange(newVal);
        }
    };

    return (
        <span style={{
            display: 'inline-flex',
            alignItems: 'baseline', // Align the input exactly to the baseline of the surrounding paragraph text
            fontFamily: '"Courier New", Courier, monospace', /* Enforce Monospace for accurate slot rendering */
            fontSize: '18px',
            lineHeight: 1.8, // Increased line-height to prevent vertical crowding (Fixes Bug #3)
            whiteSpace: 'nowrap' // Prevent breaking the word mid-way across lines
        }}>
            {/* The static prefix of the word (e.g., 'wat' from 'watches') */}
            {prefix && (
                <span style={{
                    // Fix Bug #1: Intra-word Fracture. Zero margin between prefix and input.
                    marginRight: '0px',
                    paddingRight: '0px'
                }}>{prefix}</span>
            )}

            {/* The responsive input masquerading as character slots */}
            <input
                type="text"
                className="ets-cloze-box"
                value={value}
                onChange={handleChange}
                maxLength={targetLength}
                spellCheck={false}
                autoComplete="off"
                style={{
                    // Exact sizing based on character units (ch)
                    width: `${targetLength}ch`,
                    padding: 0,
                    margin: 0,
                    border: 'none',
                    outline: 'none',
                    background: 'transparent',
                    fontFamily: 'inherit',
                    fontSize: 'inherit',
                    lineHeight: 'inherit',
                    color: '#005587', // ETS Blue for student input
                    fontWeight: 600,

                    // Fix Bug #4 & #2: Heavy Dominance & Gap confusion. 
                    // Draw a VERY soft, subtle dashed line at the bottom.
                    // 90% underline, 10% gap to signify individual letters without fracturing the word shape.
                    backgroundImage: 'linear-gradient(to right, #B0B0B0 90%, transparent 10%)',
                    backgroundPosition: 'bottom left',
                    backgroundSize: '1ch 1.5px', // Extremely thin (1.5px) to remove visual heavy dominance
                    backgroundRepeat: 'repeat-x',

                    // Tighten up letter spacing so they sit neatly on their respective dashes
                    letterSpacing: '0ch',
                    paddingLeft: '0.1ch',
                    // Force the cursor/text to align properly with the dash baseline
                    textAlign: 'left',
                    verticalAlign: 'baseline'
                }}
                aria-label={`Fill in the remaining ${targetLength} characters`}
            />
        </span>
    );
};
