"use client";

import React, { useState } from "react";

interface QuestionStatement {
    questionNumber: number | string;
    text: string;
}

interface MatchingMatrixProps {
    questions: QuestionStatement[];
    paragraphLetters: string[];
    onAnswerChange?: (answers: Record<string, string>) => void;
}

export default function MatchingMatrix({
    questions,
    paragraphLetters,
    onAnswerChange,
}: MatchingMatrixProps) {
    const [answers, setAnswers] = useState<Record<string, string>>({});

    const handleCellClick = (qNum: string | number, para: string) => {
        setAnswers((prev) => {
            const currentSelected = prev[qNum];
            const newSelected = currentSelected === para ? "" : para;
            const newAnswers = { ...prev, [qNum]: newSelected };
            if (onAnswerChange) onAnswerChange(newAnswers);
            return newAnswers;
        });
    };

    return (
        <div
            className="flex flex-col gap-4 w-full overflow-x-auto pb-2"
            style={{ fontFamily: "var(--ielts-font)" }}
        >
            <div className="overflow-hidden" style={{ border: "1px solid var(--ielts-border-default)" }}>
                <table className="w-full text-left border-collapse" style={{ minWidth: "500px" }}>
                    <thead>
                        <tr style={{ backgroundColor: "var(--ielts-instruction-bar-bg)" }}>
                            <th
                                style={{
                                    padding: "10px 12px",
                                    fontWeight: 700,
                                    color: "#333",
                                    width: "40px",
                                    textAlign: "center",
                                    borderBottom: "1px solid var(--ielts-border-default)",
                                }}
                            />
                            <th
                                style={{
                                    padding: "10px 12px",
                                    fontWeight: 600,
                                    color: "#333",
                                    minWidth: "200px",
                                    borderBottom: "1px solid var(--ielts-border-default)",
                                }}
                            />
                            {paragraphLetters.map((letter) => (
                                <th
                                    key={letter}
                                    style={{
                                        padding: "10px 8px",
                                        fontWeight: 700,
                                        color: "#333",
                                        textAlign: "center",
                                        minWidth: "44px",
                                        borderBottom: "1px solid var(--ielts-border-default)",
                                    }}
                                >
                                    {letter}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {questions.map((q) => (
                            <tr
                                key={q.questionNumber}
                                style={{ borderBottom: "1px solid #e5e5e5" }}
                            >
                                <td
                                    style={{
                                        padding: "10px 12px",
                                        fontWeight: 700,
                                        color: "#333",
                                        textAlign: "center",
                                        verticalAlign: "top",
                                        fontSize: "14px",
                                    }}
                                >
                                    {q.questionNumber}
                                </td>
                                <td
                                    style={{
                                        padding: "10px 12px",
                                        color: "#333",
                                        fontSize: "16px",
                                        lineHeight: 1.5,
                                        verticalAlign: "top",
                                    }}
                                >
                                    {q.text}
                                </td>
                                {paragraphLetters.map((letter) => {
                                    const isSelected = answers[q.questionNumber] === letter;
                                    return (
                                        <td
                                            key={letter}
                                            style={{
                                                padding: "6px",
                                                textAlign: "center",
                                                verticalAlign: "middle",
                                                backgroundColor: isSelected
                                                    ? "var(--ielts-row-highlight)"
                                                    : "transparent",
                                                cursor: "pointer",
                                            }}
                                            onClick={() => handleCellClick(q.questionNumber, letter)}
                                        >
                                            <div
                                                className="flex justify-center"
                                                style={{ padding: "4px" }}
                                            >
                                                <div
                                                    style={{
                                                        width: "13px",
                                                        height: "13px",
                                                        borderRadius: "50%",
                                                        border: `1px solid ${isSelected ? "var(--ielts-active-blue)" : "#999"}`,
                                                        display: "flex",
                                                        alignItems: "center",
                                                        justifyContent: "center",
                                                    }}
                                                >
                                                    {isSelected && (
                                                        <div
                                                            style={{
                                                                width: "7px",
                                                                height: "7px",
                                                                borderRadius: "50%",
                                                                backgroundColor: "var(--ielts-active-blue)",
                                                            }}
                                                        />
                                                    )}
                                                </div>
                                            </div>
                                        </td>
                                    );
                                })}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
