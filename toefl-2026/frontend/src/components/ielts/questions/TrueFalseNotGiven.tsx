"use client";

import React, { useState } from "react";

type TFNGChoice = "TRUE" | "FALSE" | "NOT GIVEN" | "YES" | "NO" | null;

interface TFNGQuestionProps {
    questionNumber: number;
    questionText: string;
    type?: "TFNG" | "YNNG";
    onAnswerChange?: (choice: TFNGChoice) => void;
}

export default function TrueFalseNotGiven({
    questionNumber,
    questionText,
    type = "TFNG",
    onAnswerChange,
}: TFNGQuestionProps) {
    const [selected, setSelected] = useState<TFNGChoice>(null);
    const [struckOut, setStruckOut] = useState<TFNGChoice[]>([]);

    const options: TFNGChoice[] =
        type === "TFNG" ? ["TRUE", "FALSE", "NOT GIVEN"] : ["YES", "NO", "NOT GIVEN"];

    const handleOptionClick = (option: TFNGChoice) => {
        // Click selected = deselect (real CD-IELTS behavior)
        const newSelection = selected === option ? null : option;
        setSelected(newSelection);
        if (onAnswerChange) onAnswerChange(newSelection);
    };

    const handleRightClick = (e: React.MouseEvent, option: TFNGChoice) => {
        e.preventDefault();
        setStruckOut((prev) =>
            prev.includes(option) ? prev.filter((o) => o !== option) : [...prev, option]
        );
    };

    return (
        <div
            className="flex flex-col gap-2 py-4 px-5"
            style={{ fontFamily: "var(--ielts-font)" }}
        >
            {/* Question text */}
            <div className="flex gap-4 items-start">
                <span
                    data-question-id={questionNumber}
                    className="shrink-0 flex items-center justify-center mt-[2px]"
                    style={{
                        width: "28px",
                        height: "28px",
                        fontWeight: 700,
                        fontSize: "14px",
                        color: selected ? "var(--ielts-active-blue)" : "#333",
                        border: selected
                            ? "2px solid var(--ielts-active-blue)"
                            : "1px solid #999",
                        borderRadius: "2px",
                    }}
                >
                    {questionNumber}
                </span>

                <div className="flex flex-col gap-3">
                    <p style={{ fontSize: "16px", color: "#333", lineHeight: 1.5, paddingTop: "3px" }}>
                        {questionText}
                    </p>

                    {/* Radio options — aligned with text */}
                    <div className="flex flex-col gap-1">
                        {options.map((option) => {
                            const isSelected = selected === option;
                            const isStruckOut = struckOut.includes(option);

                            return (
                                <label
                                    key={option}
                                    className="flex items-center gap-4 cursor-pointer py-[6px] px-1 rounded-sm transition-colors" // Increased gap to 4, reduced py/px
                                    style={{
                                        backgroundColor: isSelected ? "var(--ielts-row-highlight)" : "transparent",
                                        opacity: isStruckOut ? 0.45 : 1,
                                        textDecoration: isStruckOut ? "line-through" : "none",
                                    }}
                                    onClick={(e) => {
                                        e.preventDefault();
                                        handleOptionClick(option);
                                    }}
                                    onContextMenu={(e) => handleRightClick(e, option)}
                                >
                                    {/* Radio circle */}
                                    <div
                                        className="shrink-0 flex items-center justify-center"
                                        style={{
                                            width: "14px", // Slightly larger radio circle
                                            height: "14px",
                                            borderRadius: "50%",
                                            border: `1.5px solid ${isSelected ? "var(--ielts-active-blue)" : "#666"}`, // Thicker border, darker gray when unselected
                                        }}
                                    >
                                        {isSelected && (
                                            <div
                                                style={{
                                                    width: "8px", // Slightly larger inner circle
                                                    height: "8px",
                                                    borderRadius: "50%",
                                                    backgroundColor: "var(--ielts-active-blue)",
                                                }}
                                            />
                                        )}
                                    </div>

                                    <span
                                        style={{
                                            fontSize: "14px", // Matches reference text size better
                                            color: "#333",
                                            fontWeight: 400, // Text weight doesn't change on selection in reference
                                            paddingLeft: "4px",
                                            letterSpacing: "0.01em",
                                        }}
                                    >
                                        {option}
                                    </span>

                                    <input
                                        type="radio"
                                        name={`q-${questionNumber}`}
                                        value={option || ""}
                                        checked={isSelected}
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
