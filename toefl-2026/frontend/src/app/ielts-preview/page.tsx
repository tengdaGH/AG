"use client";

import React, { useState } from "react";
import MultipleChoiceQuestion from "@/components/ielts/questions/MultipleChoiceQuestion";
import MatchingMatrix from "@/components/ielts/questions/MatchingMatrix";
import DiagramLabeling from "@/components/ielts/questions/DiagramLabeling";
import InlineCompletion from "@/components/ielts/questions/InlineCompletion";
import TrueFalseNotGiven from "@/components/ielts/questions/TrueFalseNotGiven";
import HeadingMatcher from "@/components/ielts/questions/HeadingMatcher";
import GapFill from "@/components/ielts/questions/GapFill";
import GapFillItem from "@/components/ielts/questions/GapFillItem";
import MatchingItem from "@/components/ielts/questions/MatchingItem";

export default function IeltsComponentsPreview() {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const [answers, setAnswers] = useState<Record<string, any>>({});

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const handleAnswerChange = (key: string, val: any) => {
        setAnswers((prev) => ({ ...prev, [key]: val }));
    };

    return (
        <div className="min-h-screen bg-[#F5F7FA] p-8 font-sans">
            <h1 className="text-3xl font-bold mb-8 text-[#002D62] text-center">IELTS Authentic UI Components Preview</h1>

            <div className="max-w-4xl mx-auto space-y-12">

                {/* 1. Multiple Choice */}
                <section className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <h2 className="text-xl font-bold mb-4 border-b pb-2">1. Multiple Choice (with Right-click Strikeout)</h2>
                    <p className="text-sm text-gray-500 mb-6">Instruction: Left click to select a choice. Right-click to strike out an option.</p>
                    <MultipleChoiceQuestion
                        questionNumber={14}
                        text="What is the main purpose of the first paragraph?"
                        options={[
                            { letter: "A", text: "To describe the discovery of the ancient city." },
                            { letter: "B", text: "To explain the methodology used by researchers." },
                            { letter: "C", text: "To outline the early life of the lead archaeologist." },
                            { letter: "D", text: "To highlight the historical significance of the region." }
                        ]}
                        multi={false}
                        onAnswerChange={(ans) => handleAnswerChange('mcq_14', ans)}
                    />
                    <div className="mt-4 text-sm text-green-600 font-mono">Current State: {JSON.stringify(answers['mcq_14'])}</div>
                </section>

                {/* 2. Matching Matrix */}
                <section className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <h2 className="text-xl font-bold mb-4 border-b pb-2">2. Matching Information (Matrix)</h2>
                    <p className="text-sm text-gray-500 mb-6">Instruction: Click a cell to assign a paragraph to a statement.</p>
                    <MatchingMatrix
                        questions={[
                            { questionNumber: 27, text: "A description of the early trade routes." },
                            { questionNumber: 28, text: "An explanation of why the empire collapsed." },
                            { questionNumber: 29, text: "Examples of the architectural styles." },
                        ]}
                        paragraphLetters={["A", "B", "C", "D", "E"]}
                        onAnswerChange={(ans) => handleAnswerChange('matching_matrix', ans)}
                    />
                    <div className="mt-4 text-sm text-green-600 font-mono">Current State: {JSON.stringify(answers['matching_matrix'])}</div>
                </section>

                {/* 3. Inline Completion (Summary) */}
                <section className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <h2 className="text-xl font-bold mb-4 border-b pb-2">3. Inline Summary Completion</h2>
                    <p className="text-sm text-gray-500 mb-6">Instruction: Type into the inline gaps exactly like the authentic CBT interface.</p>
                    <InlineCompletion
                        text="The research indicated that [GAP_31] were the primary cause of the degradation in the outer layers. However, scientists also noted that the presence of [GAP_32] could accelerate the process significantly under these conditions."
                        wordLimit={2}
                        onAnswerChange={(ans) => handleAnswerChange('inline_summary', ans)}
                    />
                    <div className="mt-4 text-sm text-green-600 font-mono">Current State: {JSON.stringify(answers['inline_summary'])}</div>
                </section>

                {/* 4. Diagram Labeling */}
                <section className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <h2 className="text-xl font-bold mb-4 border-b pb-2">4. Diagram Labeling</h2>
                    <p className="text-sm text-gray-500 mb-6">Instruction: Enter labels based on visual diagram.</p>
                    <DiagramLabeling
                        imageUrl="https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/Water_cycle_blank.svg/800px-Water_cycle_blank.svg.png"
                        labels={[
                            { questionNumber: 36, xPercent: 15, yPercent: 40 },
                            { questionNumber: 37, xPercent: 65, yPercent: 20 },
                            { questionNumber: 38, xPercent: 85, yPercent: 60 }
                        ]}
                        onAnswerChange={(ans) => handleAnswerChange('diagram', ans)}
                    />
                    <div className="mt-4 text-sm text-green-600 font-mono">Current State: {JSON.stringify(answers['diagram'])}</div>
                </section>

                {/* 5. True/False/Not Given */}
                <section className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <h2 className="text-xl font-bold mb-4 border-b pb-2">5. True/False/Not Given (with Strikeout)</h2>
                    <p className="text-sm text-gray-500 mb-6">Instruction: Left click to select a choice. Right-click to strike out an option.</p>
                    <TrueFalseNotGiven
                        questionNumber={40}
                        questionText="The discovery of the new species changes our understanding of evolution."
                        type="TFNG"
                        onAnswerChange={(ans) => handleAnswerChange('tfng_40', ans)}
                    />
                    <div className="mt-4 text-sm text-green-600 font-mono">Current State: {JSON.stringify(answers['tfng_40'])}</div>
                </section>

                {/* 6. Heading Matcher */}
                <section className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <h2 className="text-xl font-bold mb-4 border-b pb-2">6. Matching Headings (Drag & Drop)</h2>
                    <p className="text-sm text-gray-500 mb-6">Instruction: Drag a heading from the bank to a paragraph drop zone.</p>
                    <HeadingMatcher
                        headings={[
                            { id: "i", text: "The effects of climate change on migration" },
                            { id: "ii", text: "Historical perspectives on trade" },
                            { id: "iii", text: "New farming techniques in the 20th century" },
                            { id: "iv", text: "The economic impact of the discovery" }
                        ]}
                        questions={[
                            { questionNumber: 1, paragraphLetter: "A" },
                            { questionNumber: 2, paragraphLetter: "B" },
                            { questionNumber: 3, paragraphLetter: "C" }
                        ]}
                        onAnswerChange={(ans) => handleAnswerChange('headings', ans)}
                    />
                    <div className="mt-4 text-sm text-green-600 font-mono">Current State: {JSON.stringify(answers['headings'])}</div>
                </section>

                {/* 7. Gap Fill (Standard) */}
                <section className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <h2 className="text-xl font-bold mb-4 border-b pb-2">7. Standard Gap Fill</h2>
                    <GapFill
                        questionNumber={5}
                        textBefore="The minimum age for the new driving license is"
                        textAfter="years."
                        wordLimit={1}
                        onAnswerChange={(ans) => handleAnswerChange('gapfill_5', ans)}
                    />
                    <div className="mt-4 text-sm text-green-600 font-mono">Current State: {JSON.stringify(answers['gapfill_5'])}</div>
                </section>

                {/* 8. Gap Fill (Item / Flowchart) */}
                <section className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <h2 className="text-xl font-bold mb-4 border-b pb-2">8. Flowchart / Table Gap Fill Item</h2>
                    <div className="bg-[#f9f9f9] p-4 font-mono text-sm border-l-4 border-blue-500">
                        Stage 1: Collect data using the <GapFillItem questionNumber={8} wordLimit={2} onAnswerChange={(ans) => handleAnswerChange('gapfillitem_8', ans)} /> tool.
                    </div>
                    <div className="mt-4 text-sm text-green-600 font-mono">Current State: {JSON.stringify(answers['gapfillitem_8'])}</div>
                </section>

                {/* 9. Matching Item (Single input box) */}
                <section className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <h2 className="text-xl font-bold mb-4 border-b pb-2">9. Categorization / Matching Item</h2>
                    <p className="text-sm text-gray-500 mb-6">Instruction: Type the correct letter in the box.</p>
                    <MatchingItem
                        questionNumber={12}
                        promptText="Believed that human behavior is largely determined by genetics."
                        options={[
                            { id: "A", text: "Researcher Smith" },
                            { id: "B", text: "Researcher Jones" }
                        ]}
                        showOptionsGrid={true}
                        onAnswerChange={(ans) => handleAnswerChange('matchingitem_12', ans)}
                    />
                    <div className="mt-4 text-sm text-green-600 font-mono">Current State: {JSON.stringify(answers['matchingitem_12'])}</div>
                </section>

            </div>
        </div>
    );
}
