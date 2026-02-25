import React, { useState } from "react";

interface GapFillProps {
    questionNumber: number;
    textBefore: string;
    textAfter: string;
    wordLimit: number;
    onAnswerChange?: (answer: string) => void;
}

export default function GapFill({
    questionNumber,
    textBefore,
    textAfter,
    wordLimit,
    onAnswerChange,
}: GapFillProps) {
    const [value, setValue] = useState("");

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const newVal = e.target.value;
        const words = newVal.trim() ? newVal.trim().split(/\s+/) : [];

        let finalVal = newVal;
        if (words.length > wordLimit) {
            finalVal = words.slice(0, wordLimit).join(" ");
        }

        setValue(finalVal);
        if (onAnswerChange) {
            onAnswerChange(finalVal);
        }
    };

    return (
        <div className="flex gap-4 py-5 border-b border-[#E5E5EA] last:border-0 hover:bg-gray-50/50 p-4 rounded-md transition-colors items-center flex-wrap">
            <span className="font-bold text-gray-800 text-lg w-8 shrink-0">{questionNumber}</span>
            <span className="text-gray-900 leading-relaxed font-medium text-[15px]">{textBefore}</span>
            <input
                type="text"
                value={value}
                onChange={handleChange}
                className="
          border-2 !border-[#111111] focus:!border-[#002D62] focus:ring-1 focus:ring-[#002D62]
          focus:outline-none px-3 min-h-[44px] mx-2 w-48 bg-white transition-all
          font-semibold text-gray-900 text-[15px] placeholder:text-[#8E8E93] shadow-sm rounded-none
        "
                placeholder=""
            />
            <span className="text-gray-900 leading-relaxed font-medium text-[15px]">{textAfter}</span>
        </div>
    );
}
