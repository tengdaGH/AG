import React from "react";

interface QuestionBlockProps {
    instructions: string | React.ReactNode;
    questionRange?: string;
    children: React.ReactNode;
}

export default function QuestionBlock({
    instructions,
    questionRange,
    children,
}: QuestionBlockProps) {
    return (
        <div
            className="flex flex-col gap-0 mb-8"
            style={{ fontFamily: "var(--ielts-font)" }}
        >
            {/* Instruction bar — Inspera style */}
            <div
                style={{
                    backgroundColor: "var(--ielts-instruction-bar-bg)",
                    padding: "10px 16px",
                    borderBottom: "1px solid var(--ielts-border-default)",
                }}
            >
                {questionRange && (
                    <div
                        style={{
                            fontWeight: 700,
                            fontSize: "15px",
                            color: "var(--ielts-text-primary)",
                            marginBottom: "4px",
                        }}
                    >
                        {questionRange}
                    </div>
                )}
                <div
                    style={{
                        fontSize: "14px",
                        color: "#555",
                        lineHeight: 1.5,
                    }}
                >
                    {instructions}
                </div>
            </div>

            {/* Questions */}
            <div
                style={{
                    backgroundColor: "#fff",
                    border: "1px solid var(--ielts-border-default)",
                    borderTop: "none",
                }}
            >
                {children}
            </div>
        </div>
    );
}
