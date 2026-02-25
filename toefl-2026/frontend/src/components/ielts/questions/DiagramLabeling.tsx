"use client";

import React, { useState } from "react";

interface LabelPosition {
    questionNumber: number | string;
    xPercent: number; // 0 to 100
    yPercent: number; // 0 to 100
    width?: number; // Optional custom width
}

interface DiagramLabelingProps {
    imageUrl: string;
    imageAlt?: string;
    labels: LabelPosition[];
    onAnswerChange?: (answers: Record<string, string>) => void; // mapping: questionNumber -> text
}

export default function DiagramLabeling({
    imageUrl,
    imageAlt = "Diagram to label",
    labels,
    onAnswerChange
}: DiagramLabelingProps) {
    const [answers, setAnswers] = useState<Record<string, string>>({});
    const [focusedLabel, setFocusedLabel] = useState<string | number | null>(null);

    const handleInputChange = (qNum: string | number, val: string) => {
        setAnswers(prev => {
            const newAnswers = { ...prev, [qNum]: val };
            if (onAnswerChange) {
                onAnswerChange(newAnswers);
            }
            return newAnswers;
        });
    };

    return (
        <div className="flex flex-col gap-6 animate-fade-in mb-12">
            <div className="bg-[#E6E8ED] px-5 py-3 border-l-4 border-[#002D62] shadow-sm rounded-r-md">
                <div className="font-semibold text-gray-700 text-[14px]">
                    Label the diagram below. Choose NO MORE THAN TWO WORDS from the passage for each answer.
                </div>
            </div>

            <div className="relative border border-gray-200 shadow-sm rounded-md bg-white p-4 overflow-auto min-h-[400px] flex items-center justify-center">
                <div className="relative inline-block max-w-full">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                        src={imageUrl}
                        alt={imageAlt}
                        className="max-w-full h-auto object-contain block"
                    />

                    {labels.map(label => {
                        const isFocused = focusedLabel === label.questionNumber;
                        return (
                            <div
                                key={label.questionNumber}
                                className="absolute flex items-center gap-2 transform -translate-y-1/2"
                                style={{
                                    left: `${label.xPercent}%`,
                                    top: `${label.yPercent}%`,
                                    width: label.width ? `${label.width}px` : 'auto'
                                }}
                            >
                                <span className="font-bold text-gray-800 text-lg bg-white/80 px-1 rounded shadow-sm shrink-0 border border-gray-100">
                                    {label.questionNumber}
                                </span>
                                <div className="relative">
                                    <input
                                        type="text"
                                        value={answers[label.questionNumber] || ""}
                                        onChange={(e) => handleInputChange(label.questionNumber, e.target.value)}
                                        onFocus={() => setFocusedLabel(label.questionNumber)}
                                        onBlur={() => setFocusedLabel(null)}
                                        className="
                                            h-9 border-2 border-gray-800 rounded-sm bg-white shadow-md transition-all outline-none 
                                            focus:border-[#002D62] focus:ring-1 focus:ring-[#002D62] font-bold text-gray-900 text-[14px] 
                                            px-2 w-32 md:w-40
                                        "
                                        placeholder=""
                                    />
                                    {/* Visual focus indicator underline */}
                                    <div className={`
                                        absolute -bottom-1 left-1/2 -translate-x-1/2 h-1 bg-[#002D62] transition-all duration-300 rounded-t-sm
                                        ${isFocused ? "w-11/12 opacity-100" : "w-0 opacity-0"}
                                    `} />
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
