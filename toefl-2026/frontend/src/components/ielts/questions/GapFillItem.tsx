"use client";

import React, { useState } from "react";

interface GapFillItemProps {
    questionNumber: number | string;
    textBefore?: string | React.ReactNode;
    textAfter?: string | React.ReactNode;
    contentHtml?: string;
    wordLimit?: number;
    onAnswerChange?: (answer: string) => void;
}

export default function GapFillItem({
    questionNumber,
    textBefore,
    textAfter,
    contentHtml,
    wordLimit,
    onAnswerChange,
}: GapFillItemProps) {
    const [value, setValue] = useState("");
    const [isFocused, setIsFocused] = useState(false);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const newVal = e.target.value;
        setValue(newVal);
        if (onAnswerChange) onAnswerChange(newVal);
    };

    const handlePaste = (e: React.ClipboardEvent) => {
        const pasteData = e.clipboardData.getData("text");
        const words = pasteData.trim().split(/\s+/);
        if (wordLimit && words.length > wordLimit) {
            console.warn(`Pasted text exceeds ${wordLimit} word limit.`);
        }
    };

    const inputElement = (
        <input
            type="text"
            data-question-id={questionNumber}
            value={value}
            onChange={handleChange}
            onPaste={handlePaste}
            placeholder={String(questionNumber)}
            style={{
                display: "inline-block",
                width: "144px",
                height: "22px",
                border: "1px solid var(--ielts-input-border)",
                borderRadius: "3px",
                fontFamily: "var(--ielts-font)",
                fontSize: "16px",
                color: "#000",
                padding: "0 8px",
                outline: "none",
                verticalAlign: "middle",
                margin: "0 4px",
                transition: "border-color 0.15s, box-shadow 0.15s",
                borderColor: isFocused ? "rgb(65, 142, 200)" : "var(--ielts-input-border)",
                boxShadow: isFocused ? "rgb(65, 142, 200) 0px 0px 0px 1px" : "none",
            }}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
        />
    );

    if (contentHtml) {
        // Regex to find the marker: e.g., "7........" or "(7)_____" or " 7 ... "
        // Specifically look for the question number optionally wrapped in parens, followed closely by multiple dots or underscores
        const markerRegex = new RegExp(`(?:\\(\\s*)?${questionNumber}(?:\\s*\\))?\\s*[._]{2,}`, "gi");
        const parts = contentHtml.split(markerRegex);

        return (
            <div className="py-2" style={{ fontFamily: "var(--ielts-font)" }}>
                {parts.map((part, index) => (
                    <React.Fragment key={index}>
                        <span
                            style={{ fontSize: "16px", color: "#333", lineHeight: 1.5 }}
                            dangerouslySetInnerHTML={{ __html: part }}
                        />
                        {index < parts.length - 1 && inputElement}
                    </React.Fragment>
                ))}
            </div>
        );
    }

    return (
        <div
            className="flex gap-3 py-3 px-5 items-center flex-wrap"
            style={{ fontFamily: "var(--ielts-font)" }}
        >
            <span
                className="shrink-0 flex items-center justify-center"
                style={{
                    width: "28px",
                    height: "28px",
                    fontWeight: 700,
                    fontSize: "14px",
                    color: value ? "var(--ielts-active-blue)" : "#333",
                    border: value
                        ? "2px solid var(--ielts-active-blue)"
                        : "1px solid #999",
                    borderRadius: "2px",
                }}
            >
                {questionNumber}
            </span>

            {textBefore && (
                <span style={{ fontSize: "16px", color: "#333", lineHeight: 1.5 }}>
                    {textBefore}
                </span>
            )}

            {inputElement}

            {textAfter && (
                <span style={{ fontSize: "16px", color: "#333", lineHeight: 1.5 }}>
                    {textAfter}
                </span>
            )}
        </div>
    );
}
