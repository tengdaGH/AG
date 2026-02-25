"use client";

import React from "react";
import QuestionBlock from "@/components/ielts/questions/QuestionBlock";
import MultipleChoiceItem from "@/components/ielts/questions/MultipleChoiceItem";
import MatchingItem from "@/components/ielts/questions/MatchingItem";
import GapFillItem from "@/components/ielts/questions/GapFillItem";

export default function IeltsComponentsPreview() {
    return (
        <div className="min-h-screen bg-[#F5F7FA] p-8 md:p-16 text-gray-900 font-sans max-w-4xl mx-auto flex flex-col gap-12">
            <h1 className="text-3xl font-bold text-[#002D62] mb-4 border-b-2 border-[#002D62] pb-4">IELTS Core Components Visual Verification</h1>

            {/* TYPE 1: Multiple Choice (Single) */}
            <section>
                <h2 className="text-xl font-bold mb-4">1. Multiple Choice (Choose one letter)</h2>
                <QuestionBlock instructions="Choose the correct letter, A, B, C or D." questionRange="Question 1">
                    <MultipleChoiceItem
                        questionNumber={1}
                        text="What is the main purpose of the passage?"
                        options={[
                            { id: "A", text: "To describe a historical event" },
                            { id: "B", text: "To argue for a new scientific theory" },
                            { id: "C", text: "To compare two different educational approaches" },
                            { id: "D", text: "To explain the origins of a particular language" }
                        ]}
                    />
                </QuestionBlock>
            </section>

            {/* TYPE 2 & 3: TRUE/FALSE/NOT GIVEN or YES/NO/NOT GIVEN */}
            <section>
                <h2 className="text-xl font-bold mb-4">2 & 3. Identifying Information / Views (T/F/NG)</h2>
                <QuestionBlock instructions="Do the following statements agree with the information given in Reading Passage 1? Write TRUE, FALSE, or NOT GIVEN." questionRange="Questions 2-3">
                    <MultipleChoiceItem
                        questionNumber={2}
                        text="The author believes that climate change is irreversible."

                        options={[
                            { id: "TRUE" },
                            { id: "FALSE" },
                            { id: "NOT GIVEN" }
                        ]}
                    />
                    <MultipleChoiceItem
                        questionNumber={3}
                        text="Solar energy will become the dominant energy source by 2050."

                        options={[
                            { id: "YES" },
                            { id: "NO" },
                            { id: "NOT GIVEN" }
                        ]}
                    />
                </QuestionBlock>
            </section>

            {/* TYPE 4 & 5: Matching Information / Headings */}
            <section>
                <h2 className="text-xl font-bold mb-4">4 & 5. Matching Information / Headings</h2>
                <QuestionBlock instructions="Reading Passage 2 has seven paragraphs, A-G. Choose the correct heading for each paragraph from the list of headings below." questionRange="Questions 4-5">
                    <div className="p-4 border-b border-[#E5E5EA]">
                        <p className="font-bold text-sm text-gray-700 mb-3 uppercase">List of Headings</p>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[14px]">
                            <div className="flex gap-2"><span className="font-bold">i</span> The role of the government</div>
                            <div className="flex gap-2"><span className="font-bold">ii</span> Future challenges</div>
                            <div className="flex gap-2"><span className="font-bold">iii</span> Economic factors</div>
                            <div className="flex gap-2"><span className="font-bold">iv</span> Social implications</div>
                        </div>
                    </div>
                    <MatchingItem
                        questionNumber={4}
                        promptText="Paragraph A"
                        options={[]}
                    />
                    <MatchingItem
                        questionNumber={5}
                        promptText="Paragraph B"
                        options={[]}
                    />
                </QuestionBlock>
            </section>

            {/* TYPE 6: Matching Features */}
            <section>
                <h2 className="text-xl font-bold mb-4">6. Matching Features</h2>
                <QuestionBlock instructions="Look at the following statements and the list of researchers below. Match each statement with the correct researcher, A, B or C." questionRange="Questions 6-7">
                    <MatchingItem
                        questionNumber={6}
                        promptText="Argued that language is innate."
                        showOptionsGrid={true}
                        options={[
                            { id: "A", text: "Noam Chomsky" },
                            { id: "B", text: "B.F. Skinner" },
                            { id: "C", text: "Jean Piaget" }
                        ]}
                    />
                    <MatchingItem
                        questionNumber={7}
                        promptText="Proposed the theory of cognitive development."
                        options={[]} // Assumes shared bank but we rendered it once above via the component logic for demo, though we'd usually put it outside
                    />
                </QuestionBlock>
            </section>

            {/* TYPE 7, 8, 9, 10, 11: Gap Fill Item Types */}
            <section>
                <h2 className="text-xl font-bold mb-4">7, 8, 9, 10, 11. Sentence/Summary Completion & Short Answer</h2>
                <QuestionBlock instructions="Complete the sentences below. Choose ONE WORD ONLY from the passage for each answer." questionRange="Questions 8-9">
                    <GapFillItem
                        questionNumber={8}
                        textBefore="The most significant advantage of the new system is its"
                        textAfter="efficiency."
                        wordLimit={1}
                    />
                    <GapFillItem
                        questionNumber={9}
                        textBefore="Many critics argue that the plan lacks"
                        textAfter="and therefore will fail."
                        wordLimit={1}
                    />
                </QuestionBlock>

                <div className="mt-8" />

                <QuestionBlock instructions="Answer the questions below. Choose NO MORE THAN THREE WORDS AND/OR A NUMBER from the passage." questionRange="Questions 10-11">
                    <GapFillItem
                        questionNumber={10}
                        textBefore="What material was used to construct the earliest bridges?"
                        wordLimit={3}
                    />
                    <GapFillItem
                        questionNumber={11}
                        textBefore="In what year did the revolution begin?"
                        wordLimit={3}
                    />
                </QuestionBlock>
            </section>
        </div>
    );
}
