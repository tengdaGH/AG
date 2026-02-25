"use client";

import React from "react";
import { ChevronLeft, ChevronRight, Keyboard } from "lucide-react";

export type QuestionState = {
    id: number;
    answered: boolean;
    markedForReview: boolean;
};

interface FooterNavigationProps {
    questions: QuestionState[];
    currentQuestionId: number;
    onQuestionClick: (id: number) => void;
    onReviewToggle: (id: number) => void;
    onSettingsClick: () => void;
    partLabel?: string;
}

export default function FooterNavigation({
    questions,
    currentQuestionId,
    onQuestionClick,
    onReviewToggle,
    onSettingsClick,
    partLabel,
}: FooterNavigationProps) {
    return (
        <footer
            className="flex items-center justify-between px-6 w-full flex-shrink-0 z-50 bg-white"
            style={{
                height: "64px",
                borderTop: "1px solid #d9d9d9",
                fontFamily: "var(--ielts-font)",
                boxShadow: "0 -2px 10px rgba(0,0,0,0.05)"
            }}
        >
            {/* Left: Part label */}
            <div className="flex items-center gap-4" style={{ minWidth: "160px" }}>
                <span style={{ fontSize: "14px", color: "#333", fontWeight: 700 }}>
                    {partLabel || "Part 1"}
                </span>
                {/* Removed Settings and Help buttons as they are not in the footer in the authentic UI */}
            </div>

            {/* Center: Question number grid */}
            <div className="flex items-center justify-start flex-1 overflow-hidden">
                <div
                    className="flex flex-wrap items-center max-h-[52px] overflow-y-auto"
                    style={{ gap: 0 }} // NO GAP
                >
                    {questions.map((q, idx) => {
                        const isActive = q.id === currentQuestionId;
                        const isReview = q.markedForReview;
                        const isAnswered = q.answered;

                        // To avoid double borders on adjacent items, we only draw the right border for all but the first item if neither is active.
                        // However, active item needs full border. A simpler approach is negative margin.
                        return (
                            <button
                                key={q.id}
                                onClick={() => onQuestionClick(q.id)}
                                onContextMenu={(e) => {
                                    e.preventDefault();
                                    onReviewToggle(q.id);
                                }}
                                className="relative flex items-center justify-center transition-all focus:outline-none"
                                style={{
                                    width: "30px",
                                    height: "30px",
                                    fontSize: "13px",
                                    fontWeight: isActive ? 700 : 600,
                                    fontFamily: "var(--ielts-font)",
                                    borderRadius: isReview ? "50%" : "0", // Square by default
                                    border: isActive
                                        ? "2px solid var(--ielts-active-blue)"
                                        : "1px solid #999",
                                    marginLeft: idx === 0 ? "0" : "-1px", // Collapse borders
                                    backgroundColor: isActive
                                        ? "rgba(65, 143, 198, 0.1)"
                                        : "#fff",
                                    color: isActive
                                        ? "var(--ielts-active-blue)"
                                        : "#333",
                                    zIndex: isActive ? 10 : 1, // Bring active item to front to show full border
                                }}
                            >
                                {q.id}
                                {/* Green answered bar - styled like Inspera */}
                                {isAnswered && (
                                    <div
                                        style={{
                                            position: "absolute",
                                            bottom: "0",
                                            left: "0",
                                            right: "0",
                                            height: "4px",
                                            backgroundColor: "#a0aec0", // Light grey in authentic, will verify if need green
                                        }}
                                    />
                                )}
                            </button>
                        );
                    })}
                </div>
            </div>

            {/* Right: Checkmark and Prev/Next buttons */}
            <div className="flex items-center gap-4" style={{ minWidth: "120px", justifyContent: "flex-end" }}>
                {/* Previous Button */}
                <button
                    className="flex items-center justify-center transition-colors hover:bg-black hover:bg-opacity-80"
                    style={{
                        width: "36px",
                        height: "36px",
                        backgroundColor: "#333",
                        color: "#fff",
                        borderRadius: "2px",
                    }}
                >
                    <ChevronLeft size={20} />
                </button>
                {/* Next Button */}
                <button
                    className="flex items-center justify-center transition-colors hover:bg-black hover:bg-opacity-80"
                    style={{
                        width: "36px",
                        height: "36px",
                        backgroundColor: "#111", // Slightly darker or same as prev
                        color: "#fff",
                        borderRadius: "2px",
                    }}
                >
                    <ChevronRight size={20} />
                </button>
            </div>
        </footer>
    );
}
