import React, { useState } from "react";

interface ShortAnswerProps {
    questionNumber: number;
    text?: string;
    label?: string;
    onAnswerChange?: (answer: string) => void;
}

export default function ShortAnswerQuestion({
    questionNumber,
    text,
    label,
    onAnswerChange,
}: ShortAnswerProps) {
    const [value, setValue] = useState("");

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const newVal = e.target.value;
        setValue(newVal);
        if (onAnswerChange) {
            onAnswerChange(newVal);
        }
    };

    return (
        <div className="flex flex-col gap-3 py-6 border-b border-[#E5E5EA] last:border-0 hover:bg-gray-50/50 p-6 rounded-md transition-colors">
            <div className="flex gap-4 items-start">
                <span className="font-bold text-gray-800 text-lg w-8 shrink-0" data-question-id={questionNumber}>{questionNumber}</span>
                <div className="flex flex-col gap-3 flex-1 mt-[-2px]">
                    {text && <p className="text-gray-900 leading-relaxed font-medium text-[15px]">{text}</p>}
                    <div className="flex gap-4 items-center">
                        {label && <span className="font-semibold text-gray-700 text-[15px]">{label}</span>}
                        <input
                            type="text"
                            value={value}
                            onChange={handleChange}
                            className="
                                border border-[#767676] rounded-sm focus:border-[#002D62] focus:ring-1 focus:ring-[#002D62]
                                outline-none transition-all px-3 min-h-[44px] w-full max-w-sm bg-white font-bold
                                text-gray-900 text-[15px] placeholder:text-[#8E8E93] shadow-sm
                            "
                            placeholder={`Your answer`}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
}
