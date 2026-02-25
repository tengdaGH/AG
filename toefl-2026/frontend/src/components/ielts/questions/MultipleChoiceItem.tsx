"use client";

import React, { useState } from "react";

export type OptionType = {
    id: string;
    text?: string;
};

interface MultipleChoiceItemProps {
    questionNumber: number | string;
    text: string | React.ReactNode;
    options: OptionType[];
    multi?: boolean;
    maxSelections?: number; // for multi-select: max allowed (e.g., 2 for "Pick TWO")
    onAnswerChange?: (answer: string | string[]) => void;
}

export default function MultipleChoiceItem({
    questionNumber,
    text,
    options,
    multi = false,
    maxSelections = 2,
    onAnswerChange,
}: MultipleChoiceItemProps) {
    const [selected, setSelected] = useState<string[]>([]);
    const [struckOut, setStruckOut] = useState<string[]>([]);

    const handleOptionToggle = (val: string) => {
        let newSelected: string[];
        if (multi) {
            if (selected.includes(val)) {
                // Deselect
                newSelected = selected.filter((s) => s !== val);
            } else {
                // Enforce max selections — silently ignore if at limit
                if (selected.length >= maxSelections) return;
                newSelected = [...selected, val];
            }
        } else {
            // Single: clicking selected = deselect (real CD-IELTS behavior)
            newSelected = selected.includes(val) ? [] : [val];
        }

        setSelected(newSelected);
        if (onAnswerChange) {
            onAnswerChange(multi ? newSelected : newSelected[0] || "");
        }
    };

    const handleRightClick = (e: React.MouseEvent, val: string) => {
        e.preventDefault();
        setStruckOut((prev) =>
            prev.includes(val) ? prev.filter((s) => s !== val) : [...prev, val]
        );
    };

    return (
        <div
            className="flex flex-col gap-3"
            style={{ padding: "16px 24px", fontFamily: "var(--ielts-font)" }}
        >
            {/* Question text */}
            <div className="flex gap-4 items-start">
                <span
                    data-question-id={questionNumber}
                    className="shrink-0 flex items-center justify-center"
                    style={{
                        width: "28px",
                        height: "28px",
                        fontWeight: 700,
                        fontSize: "14px",
                        color: selected.length > 0 ? "var(--ielts-active-blue)" : "#333",
                        border: selected.length > 0
                            ? "2px solid var(--ielts-active-blue)"
                            : "1px solid #999",
                        borderRadius: "2px",
                    }}
                >
                    {questionNumber}
                </span>

                <div className="flex flex-col gap-5">
                    <div style={{ fontSize: "16px", color: "#333", lineHeight: "28px", margin: 0 }}>
                        {text}
                    </div>

                    {/* Options */}
                    <div className="flex flex-col gap-3">
                        {options.map((opt) => {
                            const isChecked = selected.includes(opt.id);
                            const isStruckOut = struckOut.includes(opt.id);

                            return (
                                <label
                                    key={opt.id}
                                    className={`flex items-center gap-4 cursor-pointer py-[8px] px-3 rounded-sm transition-colors w-full ${!isChecked ? "hover:bg-[#E5E5E5]" : ""}`}
                                    style={{
                                        backgroundColor: isChecked ? "#C6E0F5" : "transparent",
                                        opacity: isStruckOut ? 0.45 : 1,
                                        textDecoration: isStruckOut ? "line-through" : "none",
                                    }}
                                    onClick={(e) => {
                                        e.preventDefault();
                                        handleOptionToggle(opt.id);
                                    }}
                                    onContextMenu={(e) => handleRightClick(e, opt.id)}
                                >
                                    {/* Radio or Checkbox */}
                                    <div className="shrink-0">
                                        {multi ? (
                                            <div
                                                className="flex items-center justify-center transition-colors"
                                                style={{
                                                    width: "18px",
                                                    height: "18px",
                                                    border: isChecked
                                                        ? "none"
                                                        : "1px solid #999",
                                                    borderRadius: "2px",
                                                    backgroundColor: isChecked ? "var(--ielts-active-blue)" : "#fff",
                                                }}
                                            >
                                                {isChecked && (
                                                    <svg width="12" height="10" viewBox="0 0 12 10" fill="none">
                                                        <path
                                                            d="M1 5L4.5 8.5L11 1.5"
                                                            stroke="white"
                                                            strokeWidth="2"
                                                            strokeLinecap="round"
                                                            strokeLinejoin="round"
                                                        />
                                                    </svg>
                                                )}
                                            </div>
                                        ) : (
                                            <div
                                                className="flex items-center justify-center"
                                                style={{
                                                    width: "14px",
                                                    height: "14px",
                                                    borderRadius: "50%",
                                                    border: `1.5px solid ${isChecked ? "var(--ielts-active-blue)" : "#666"}`,
                                                }}
                                            >
                                                {isChecked && (
                                                    <div
                                                        style={{
                                                            width: "8px",
                                                            height: "8px",
                                                            borderRadius: "50%",
                                                            backgroundColor: "var(--ielts-active-blue)",
                                                        }}
                                                    />
                                                )}
                                            </div>
                                        )}
                                    </div>

                                    {/* Option text */}
                                    <span style={{ fontSize: "16px", color: "#333", lineHeight: 1.4 }}>
                                        {opt.text || opt.id}
                                    </span>

                                    <input
                                        type={multi ? "checkbox" : "radio"}
                                        name={`q-${questionNumber}`}
                                        value={opt.id}
                                        checked={isChecked}
                                        readOnly
                                        className="sr-only"
                                    />
                                </label>
                            );
                        })}
                    </div>
                </div>
            </div>
        </div>
    );
}
