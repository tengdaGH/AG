"use client";

import React, { useState } from "react";

interface Heading {
    id: string;
    text: string;
}

interface QuestionSlot {
    questionNumber: number;
    paragraphLetter: string;
}

interface HeadingMatcherProps {
    headings: Heading[];
    questions: QuestionSlot[];
    onAnswerChange?: (answers: Record<string, string>) => void;
}

export default function HeadingMatcher({
    headings,
    questions,
    onAnswerChange,
}: HeadingMatcherProps) {
    const [answers, setAnswers] = useState<Record<string, string>>({});

    const assignedHeadingIds = Object.values(answers).filter(Boolean);
    const bankHeadings = headings.filter((h) => !assignedHeadingIds.includes(h.id));

    const handleDragStart = (e: React.DragEvent, headingId: string) => {
        e.dataTransfer.setData("text/plain", headingId);
        e.dataTransfer.effectAllowed = "move";
        setTimeout(() => {
            if (e.target instanceof HTMLElement) {
                e.target.classList.add("opacity-50");
            }
        }, 0);
    };

    const handleDragEnd = (e: React.DragEvent) => {
        if (e.target instanceof HTMLElement) {
            e.target.classList.remove("opacity-50");
        }
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = "move";
    };

    const handleDropOnZone = (e: React.DragEvent, paragraphLetter: string) => {
        e.preventDefault();
        const headingId = e.dataTransfer.getData("text/plain");
        if (!headingId) return;

        setAnswers((prev) => {
            const newState = { ...prev };
            // Remove heading from any previous zone
            for (const key in newState) {
                if (newState[key] === headingId) {
                    newState[key] = "";
                    break;
                }
            }
            newState[paragraphLetter] = headingId;
            if (onAnswerChange) onAnswerChange(newState);
            return newState;
        });
    };

    const handleDropOnBank = (e: React.DragEvent) => {
        e.preventDefault();
        const headingId = e.dataTransfer.getData("text/plain");
        if (!headingId) return;

        setAnswers((prev) => {
            const newState = { ...prev };
            for (const key in newState) {
                if (newState[key] === headingId) {
                    newState[key] = "";
                }
            }
            if (onAnswerChange) onAnswerChange(newState);
            return newState;
        });
    };

    return (
        <div
            className="flex flex-col gap-5"
            style={{ fontFamily: "var(--ielts-font)" }}
        >
            {/* Heading Bank */}
            <div
                onDragOver={handleDragOver}
                onDrop={handleDropOnBank}
                style={{
                    backgroundColor: "#f8f8f8",
                    border: "1px solid var(--ielts-border-default)",
                    borderRadius: "4px",
                    padding: "16px",
                    minHeight: "80px",
                }}
            >
                <p
                    style={{
                        fontSize: "13px",
                        fontWeight: 700,
                        color: "#666",
                        marginBottom: "12px",
                        textTransform: "uppercase",
                        letterSpacing: "0.03em",
                    }}
                >
                    List of Headings
                </p>
                <div className="flex flex-wrap gap-2">
                    {bankHeadings.map((h) => (
                        <div
                            key={h.id}
                            draggable
                            onDragStart={(e) => handleDragStart(e, h.id)}
                            onDragEnd={handleDragEnd}
                            className="flex items-center gap-2 cursor-grab active:cursor-grabbing hover:shadow-md transition-shadow"
                            style={{
                                backgroundColor: "#fff",
                                border: "1px solid var(--ielts-drop-zone-border)",
                                borderRadius: "4px",
                                padding: "8px 14px",
                                fontSize: "14px",
                                color: "#333",
                                maxWidth: "100%",
                            }}
                        >
                            <span style={{ fontWeight: 700, color: "#333", minWidth: "16px" }}>
                                {h.id}
                            </span>
                            <span style={{ lineHeight: 1.3 }}>{h.text}</span>
                        </div>
                    ))}
                    {bankHeadings.length === 0 && (
                        <div
                            style={{
                                fontSize: "13px",
                                color: "#999",
                                fontStyle: "italic",
                                width: "100%",
                                textAlign: "center",
                                padding: "8px 0",
                            }}
                        >
                            All headings assigned.
                        </div>
                    )}
                </div>
            </div>

            {/* Drop Zones */}
            <div className="flex flex-col gap-2">
                {questions.map((q) => {
                    const assignedHeadingId = answers[q.paragraphLetter];
                    const assignedHeading = headings.find(
                        (h) => h.id === assignedHeadingId
                    );

                    return (
                        <div
                            key={q.paragraphLetter}
                            className="flex gap-3 items-center py-2"
                        >
                            <span
                                data-question-id={q.questionNumber}
                                style={{
                                    fontWeight: 700,
                                    fontSize: "14px",
                                    color: "#333",
                                    width: "28px",
                                    textAlign: "right",
                                    flexShrink: 0,
                                }}
                            >
                                {q.questionNumber}
                            </span>
                            <span
                                style={{
                                    fontWeight: 600,
                                    fontSize: "14px",
                                    color: "#555",
                                    width: "90px",
                                    flexShrink: 0,
                                }}
                            >
                                Paragraph {q.paragraphLetter}
                            </span>

                            <div
                                onDragOver={handleDragOver}
                                onDrop={(e) => handleDropOnZone(e, q.paragraphLetter)}
                                style={{
                                    flex: 1,
                                    minHeight: "40px",
                                    border: assignedHeading
                                        ? "1px solid var(--ielts-drop-zone-border)"
                                        : "1px dashed var(--ielts-drop-zone-border)",
                                    borderRadius: "5px",
                                    backgroundColor: assignedHeading ? "#fff" : "#fafafa",
                                    display: "flex",
                                    alignItems: "center",
                                    transition: "border-color 0.15s",
                                }}
                            >
                                {assignedHeading ? (
                                    <div
                                        draggable
                                        onDragStart={(e) =>
                                            handleDragStart(e, assignedHeading.id)
                                        }
                                        onDragEnd={handleDragEnd}
                                        className="flex items-center gap-2 cursor-grab active:cursor-grabbing w-full"
                                        style={{
                                            padding: "8px 14px",
                                            fontSize: "14px",
                                            color: "#333",
                                        }}
                                    >
                                        <span
                                            style={{
                                                fontWeight: 700,
                                                minWidth: "16px",
                                            }}
                                        >
                                            {assignedHeading.id}
                                        </span>
                                        <span style={{ lineHeight: 1.3 }}>
                                            {assignedHeading.text}
                                        </span>
                                    </div>
                                ) : (
                                    <div
                                        style={{
                                            width: "100%",
                                            textAlign: "center",
                                            fontSize: "13px",
                                            color: "#bbb",
                                        }}
                                    >
                                        {q.questionNumber}
                                    </div>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
