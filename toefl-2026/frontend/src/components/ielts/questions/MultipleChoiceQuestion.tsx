import React, { useState } from "react";

interface Option {
    letter?: string;
    text: string;
}

interface MultipleChoiceProps {
    questionNumber: number;
    text: string;
    options: (string | Option)[];
    multi?: boolean;
    onAnswerChange?: (answer: string | string[]) => void;
}

export default function MultipleChoiceQuestion({
    questionNumber,
    text,
    options,
    multi = false,
    onAnswerChange,
}: MultipleChoiceProps) {
    const [selected, setSelected] = useState<string[]>([]);
    const [struckOut, setStruckOut] = useState<string[]>([]);

    const handleOptionToggle = (val: string) => {
        let newSelected;
        if (multi) {
            if (selected.includes(val)) {
                newSelected = selected.filter(s => s !== val);
            } else {
                newSelected = [...selected, val];
            }
        } else {
            newSelected = selected.includes(val) ? [] : [val];
        }

        setSelected(newSelected);
        if (onAnswerChange) {
            onAnswerChange(multi ? newSelected : newSelected[0]);
        }
    };

    const handleRightClick = (e: React.MouseEvent, val: string) => {
        e.preventDefault();
        setStruckOut(prev =>
            prev.includes(val) ? prev.filter(s => s !== val) : [...prev, val]
        );
    };

    return (
        <div className="flex flex-col gap-3 py-5 border-b border-[#E5E5EA] last:border-0 hover:bg-gray-50/50 p-6 rounded-md transition-colors">
            <div className="flex gap-4 items-start">
                <span className="font-bold text-gray-800 text-lg w-8 shrink-0">{questionNumber}</span>
                <p className="text-gray-900 leading-relaxed font-medium text-[15px] mt-[-2px]">{text}</p>
            </div>

            <div className="flex flex-col gap-2 ml-12 mt-2">
                {options.map((opt, i) => {
                    const optionText = typeof opt === 'string' ? opt : opt.text;
                    const optionLetter = typeof opt === 'string' ? opt.charAt(0) : (opt.letter || String.fromCharCode(65 + i)); // A, B, C...
                    const isChecked = selected.includes(optionLetter);
                    const isStruckOut = struckOut.includes(optionLetter);
                    const bgClass = isChecked ? "bg-[#B8D8F0]" : "hover:bg-[#F0F2F5] bg-transparent";

                    return (
                        <label
                            key={i}
                            className={`flex items-start gap-4 cursor-pointer group p-3 rounded-sm transition-colors w-full border border-transparent ${isChecked ? 'border-[#418FC6]' : ''} ${bgClass} ${isStruckOut ? 'opacity-50' : ''}`}
                            onClick={(e) => {
                                e.preventDefault();
                                handleOptionToggle(optionLetter);
                            }}
                            onContextMenu={(e) => handleRightClick(e, optionLetter)}
                        >
                            <div className="pt-1 shrink-0">
                                {multi ? (
                                    <div className={`
                                        w-6 h-6 border-2 rounded-sm transition-colors flex items-center justify-center
                                        ${isChecked ? "bg-[#418FC6] border-[#418FC6]" : "bg-white border-gray-400 group-hover:border-gray-600"}
                                    `}>
                                        {isChecked && (
                                            <svg width="14" height="12" viewBox="0 0 12 10" fill="none" xmlns="http://www.w3.org/2000/svg">
                                                <path d="M1 5L4.5 8.5L11 1.5" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                                            </svg>
                                        )}
                                    </div>
                                ) : (
                                    <div className={`
                                        w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all
                                        ${isChecked ? "border-[#418FC6] bg-white" : "border-gray-400 group-hover:border-gray-600 bg-white"}
                                    `}>
                                        {isChecked && <div className="w-3 h-3 rounded-full bg-[#418FC6]" />}
                                    </div>
                                )}
                            </div>

                            <div className="flex gap-3 mt-[2px] w-full" style={{ fontFamily: "var(--ielts-font)" }}>
                                <span className={`font-bold min-w-[20px] ${isStruckOut ? 'text-gray-400 line-through' : 'text-[#333]'}`}>{optionLetter}</span>
                                <span className={`leading-snug text-[15px] ${isStruckOut ? 'text-gray-400 line-through' : 'text-[#333]'}`}>{optionText}</span>
                            </div>

                            <input
                                type={multi ? "checkbox" : "radio"}
                                name={`q-${questionNumber}`}
                                value={optionLetter}
                                checked={isChecked}
                                readOnly
                                className="sr-only"
                            />
                        </label>
                    );
                })}
            </div>
        </div>
    );
}
