"use client";

import React, { useState } from "react";

export type MatchingOption = {
    id: string; // The letter A, B, C... or Roman numeral i, ii, iii...
    text: string;
};

interface MatchingItemProps {
    questionNumber: number | string;
    promptText: string | React.ReactNode;
    options: MatchingOption[]; // The bank of options to render (optional if rendered elsewhere)
    showOptionsGrid?: boolean; // Whether to render the options bank inline 
    onAnswerChange?: (answer: string) => void;
}

export default function MatchingItem({
    questionNumber,
    promptText,
    options,
    showOptionsGrid = false,
    onAnswerChange
}: MatchingItemProps) {
    const [value, setValue] = useState("");
    const [isFocused, setIsFocused] = useState(false);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const newVal = e.target.value.toUpperCase();
        setValue(newVal);
        if (onAnswerChange) {
            onAnswerChange(newVal);
        }
    };

    return (
        <div className="flex flex-col gap-4 p-5 hover:bg-gray-50/50 transition-colors w-full border-b border-[#E5E5EA] last:border-0 relative">

            {showOptionsGrid && options && options.length > 0 && (
                <div className="bg-[#F8F9FA] p-4 rounded-md border border-gray-200 mb-2">
                    <p className="font-bold text-sm text-gray-700 mb-3 uppercase tracking-wider">Options</p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {options.map((opt) => (
                            <div key={opt.id} className="flex gap-3 items-start">
                                <span className="font-bold text-[#002D62] min-w-[20px] shrink-0 text-right">{opt.id}</span>
                                <span className="text-[14px] leading-snug text-gray-800">{opt.text}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            <div className="flex gap-4 items-center">
                <span className="font-bold text-gray-800 text-lg w-8 shrink-0 text-right" data-question-id={questionNumber}>{questionNumber}</span>

                {/* Input cell designed specifically for CBT Matching interaction */}
                <div className="shrink-0 relative">
                    <input
                        type="text"
                        value={value}
                        onChange={handleChange}
                        onFocus={() => setIsFocused(true)}
                        onBlur={() => setIsFocused(false)}
                        maxLength={3} // Typically 1 letter, but maybe up to 3 for Roman numerals (iii, vii etc)
                        className="
                            w-14 h-11 text-center font-bold text-lg text-[#002D62] bg-white 
                            border-2 border-gray-300 rounded-md shadow-sm outline-none transition-all
                            focus:border-[#002D62] focus:ring-2 focus:ring-[#002D62]/20 uppercase tracking-wider
                        "
                        placeholder=""
                    />

                    {/* Visual focus indicator underline */}
                    <div className={`
                        absolute -bottom-[2px] left-1/2 -translate-x-1/2 h-1 bg-[#002D62] transition-all duration-300 rounded-t-sm
                        ${isFocused ? "w-10 opacity-100" : "w-0 opacity-0"}
                    `} />
                </div>

                <div className="text-gray-900 leading-relaxed font-medium text-[15px] flex-1">
                    {promptText}
                </div>
            </div>
        </div>
    );
}
