"use client";

import React, { useState } from "react";

interface InlineCompletionProps {
    text: string; // Text containing [GAP_num] markers
    wordLimit?: number;
    onAnswerChange?: (answers: Record<string, string>) => void;
}

export default function InlineCompletion({
    text,
    wordLimit,
    onAnswerChange,
}: InlineCompletionProps) {
    const [answers, setAnswers] = useState<Record<string, string>>({});

    const gapRegex = /\[(?:GAP_)?(\d+)\]/g;
    const parts: { type: string; content?: string; qNum?: string }[] = [];
    let lastIndex = 0;
    let match;

    while ((match = gapRegex.exec(text)) !== null) {
        if (match.index > lastIndex) {
            parts.push({ type: "text", content: text.substring(lastIndex, match.index) });
        }
        parts.push({ type: "gap", qNum: match[1] });
        lastIndex = gapRegex.lastIndex;
    }
    if (lastIndex < text.length) {
        parts.push({ type: "text", content: text.substring(lastIndex) });
    }

    const handleChange = (qNum: string, val: string) => {
        let finalVal = val;
        if (wordLimit) {
            const words = val.trim() ? val.trim().split(/\s+/) : [];
            if (words.length > wordLimit) {
                finalVal = words.slice(0, wordLimit).join(" ");
            }
        }

        setAnswers((prev) => {
            const newAnswers = { ...prev, [qNum]: finalVal };
            if (onAnswerChange) onAnswerChange(newAnswers);
            return newAnswers;
        });
    };

    return (
        <div style={{ padding: "16px 24px", fontFamily: "var(--ielts-font)" }}>
            <div style={{ fontSize: "16px", color: "#333", lineHeight: 2 }}>
                {parts.map((part, index) => {
                    if (part.type === "text") {
                        return (
                            <span
                                key={`text-${index}`}
                                dangerouslySetInnerHTML={{ __html: part.content as string }}
                            />
                        );
                    } else if (part.type === "gap") {
                        const qNum = part.qNum as string;
                        return (
                            <input
                                key={`gap-${qNum}`}
                                type="text"
                                value={answers[qNum] || ""}
                                onChange={(e) => handleChange(qNum, e.target.value)}
                                placeholder={qNum}
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
                                }}
                                onFocus={(e) => {
                                    e.currentTarget.style.borderColor = "rgb(65, 142, 200)";
                                    e.currentTarget.style.boxShadow = "rgb(65, 142, 200) 0px 0px 0px 1px";
                                }}
                                onBlur={(e) => {
                                    e.currentTarget.style.borderColor = "var(--ielts-input-border)";
                                    e.currentTarget.style.boxShadow = "none";
                                }}
                            />
                        );
                    }
                    return null;
                })}
            </div>
        </div>
    );
}
