"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import IELTSHeader from "@/components/ielts/IELTSHeader";
import FooterNavigation, { QuestionState } from "@/components/ielts/FooterNavigation";
import SplitPane from "@/components/ielts/SplitPane";
import { ColorScheme, TextSize } from "@/components/ielts/AccessibilitySettings";
import TextMarkupEngine from "@/components/ielts/TextMarkupEngine";
import TrueFalseNotGiven from "@/components/ielts/questions/TrueFalseNotGiven";
import MultipleChoiceQuestion from "@/components/ielts/questions/MultipleChoiceQuestion";
import ShortAnswerQuestion from "@/components/ielts/questions/ShortAnswerQuestion";
import InlineCompletion from "@/components/ielts/questions/InlineCompletion";
import MatchingMatrix from "@/components/ielts/questions/MatchingMatrix";
import GapFillItem from "@/components/ielts/questions/GapFillItem";
import MatchingItem from "@/components/ielts/questions/MatchingItem";

// Types
interface Heading {
    id: string;
    text: string;
}

interface HeadingMatchSlot {
    questionNumber: number;
    paragraphLetter: string;
}

interface StagingItem {
    id: string;
    title: string;
    questionCount: number;
    questionTypes: string[];
}

export default function IELTSReadingDashboard() {
    const rightPaneRef = useRef<HTMLDivElement>(null);
    const leftPaneRef = useRef<HTMLDivElement>(null);

    // Dashboard State
    const [itemsList, setItemsList] = useState<StagingItem[]>([]);
    const [selectedItemId, setSelectedItemId] = useState<string>("");

    // Workspace State
    const [currentQuestionId, setCurrentQuestionId] = useState(1);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const [itemData, setItemData] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const [questions, setQuestions] = useState<QuestionState[]>([]);

    const [leftScrollTop, setLeftScrollTop] = useState(0);
    const [rightScrollTop, setRightScrollTop] = useState(0);

    const [colorScheme, setColorScheme] = useState<ColorScheme>("standard");
    const [textSize, setTextSize] = useState<TextSize>("standard");

    // Cross-panel state for Matching Headings
    const [headingAssignments, setHeadingAssignments] = useState<Record<string, string>>({});
    const [headingsBank, setHeadingsBank] = useState<Heading[]>([]);
    const [headingSlots, setHeadingSlots] = useState<HeadingMatchSlot[]>([]);

    // Fetch list of items on mount
    useEffect(() => {
        fetch('/api/ielts/staging')
            .then(res => res.json())
            .then(data => {
                setItemsList(data.items || []);
                if (data.items?.length > 0) {
                    setSelectedItemId(data.items[0].id);
                } else {
                    setLoading(false);
                    setError("No items found in staging directory.");
                }
            })
            .catch(err => {
                console.error(err);
                setError("Failed to load items list.");
                setLoading(false);
            });
    }, []);

    // Fetch specific item when selected
    useEffect(() => {
        if (!selectedItemId) return;

        setLoading(true);
        setError(null);

        fetch(`/api/ielts/staging/${selectedItemId}`)
            .then(res => {
                if (!res.ok) throw new Error("Failed to load IELTS item " + selectedItemId);
                return res.json();
            })
            .then(data => {
                setItemData(data);

                const qRange = data.question_range || [1, 13];
                const initialQStates: QuestionState[] = [];
                for (let i = qRange[0]; i <= qRange[1]; i++) {
                    initialQStates.push({
                        id: i,
                        answered: false,
                        markedForReview: false
                    });
                }
                setQuestions(initialQStates);
                if (initialQStates.length > 0) {
                    setCurrentQuestionId(initialQStates[0].id);
                }

                // Extract matching headings data for cross-panel rendering
                const matchingGroup = data.question_groups?.find(
                    (g: any) => g.type === "MATCHING_HEADINGS"
                );
                if (matchingGroup) {
                    const firstQ = matchingGroup.questions[0];
                    const headings = (firstQ?.options || []).map((opt: any) => ({
                        id: opt.label || opt.letter || opt.id,
                        text: opt.text || "",
                    }));
                    setHeadingsBank(headings);

                    const slots = matchingGroup.questions.map((q: any) => ({
                        questionNumber: q.number,
                        paragraphLetter: (q.text || "").replace(/^Paragraph\s*/i, "").trim(),
                    }));
                    setHeadingSlots(slots);
                } else {
                    setHeadingsBank([]);
                    setHeadingSlots([]);
                }

                // Clear state between items
                setHeadingAssignments({});
                setLeftScrollTop(0);
                setRightScrollTop(0);

                if (leftPaneRef.current) leftPaneRef.current.scrollTop = 0;
                if (rightPaneRef.current) rightPaneRef.current.scrollTop = 0;

                setLoading(false);
            })
            .catch(err => {
                console.error(err);
                setError(err.message);
                setLoading(false);
            });
    }, [selectedItemId]);

    const markAnswered = useCallback((questionNumbers: number[]) => {
        setQuestions(prev => prev.map(q =>
            questionNumbers.includes(q.id) ? { ...q, answered: true } : q
        ));
    }, []);

    const handleTimeExpired = () => {
        alert("Your Reading Test has concluded.");
    };

    // Global Focus/Click Listener to Sync Active Question
    useEffect(() => {
        const handleInteraction = (e: Event) => {
            const target = e.target as HTMLElement;
            if (!target) return;

            if (target.closest('footer')) return;
            if (target.closest('#dashboard-header')) return;

            const questionEl = target.closest('[data-question-id]') as HTMLElement;
            if (questionEl) {
                const idAttr = questionEl.getAttribute('data-question-id');
                if (idAttr) {
                    const id = parseInt(idAttr, 10);
                    if (!isNaN(id)) {
                        setCurrentQuestionId(id);
                    }
                }
            }
        };

        document.addEventListener('focusin', handleInteraction);
        document.addEventListener('click', handleInteraction);

        return () => {
            document.removeEventListener('focusin', handleInteraction);
            document.removeEventListener('click', handleInteraction);
        };
    }, []);

    // Footer -> scroll to question in the correct panel
    const handleQuestionClick = useCallback((id: number) => {
        setCurrentQuestionId(id);

        requestAnimationFrame(() => {
            setTimeout(() => {
                const el = document.querySelector(`[data-question-id="${id}"]`) as HTMLElement | null;
                if (!el) return;

                let scrollContainer: HTMLElement | null = el.parentElement;
                while (scrollContainer) {
                    const overflowY = getComputedStyle(scrollContainer).overflowY;
                    if (
                        (overflowY === "auto" || overflowY === "scroll") &&
                        scrollContainer.scrollHeight > scrollContainer.clientHeight
                    ) {
                        break;
                    }
                    scrollContainer = scrollContainer.parentElement;
                }

                if (scrollContainer) {
                    const containerRect = scrollContainer.getBoundingClientRect();
                    const elRect = el.getBoundingClientRect();
                    const targetScrollTop = scrollContainer.scrollTop
                        + (elRect.top - containerRect.top)
                        - (containerRect.height / 2)
                        + (elRect.height / 2);

                    scrollContainer.scrollTop = Math.max(0, targetScrollTop);
                }

                if (el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement) {
                    el.focus();
                } else {
                    const originalTransition = el.style.transition;
                    const originalBoxShadow = el.style.boxShadow;
                    const originalBorderColor = el.style.borderColor;

                    el.style.transition = "box-shadow 0.2s, border-color 0.2s";
                    el.style.boxShadow = "0 0 0 1px var(--ielts-active-blue)";
                    el.style.borderColor = "var(--ielts-active-blue)";

                    setTimeout(() => {
                        el.style.boxShadow = originalBoxShadow;
                        el.style.borderColor = originalBorderColor;
                        el.style.transition = originalTransition;
                    }, 1500);
                }
            }, 50);
        });
    }, []);

    const handleReviewToggle = (id: number) => {
        setQuestions(prev => prev.map(q =>
            q.id === id ? { ...q, markedForReview: !q.markedForReview } : q
        ));
    };

    // Heading assignments handler (shared between panels)
    const handleHeadingAssign = useCallback((newAssignments: Record<string, string>) => {
        setHeadingAssignments(newAssignments);
        const answered = headingSlots
            .filter(s => newAssignments[s.paragraphLetter] && newAssignments[s.paragraphLetter] !== "")
            .map(s => s.questionNumber);
        markAnswered(answered);
    }, [headingSlots, markAnswered]);

    // DnD handlers for left panel drop zones
    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = "move";
    };

    const handleDropOnPassageZone = (e: React.DragEvent, paragraphLetter: string) => {
        e.preventDefault();
        const headingId = e.dataTransfer.getData("text/plain");
        if (!headingId) return;

        setHeadingAssignments(prev => {
            const newState = { ...prev };
            for (const key in newState) {
                if (newState[key] === headingId) {
                    newState[key] = "";
                    break;
                }
            }
            newState[paragraphLetter] = headingId;
            const answered = headingSlots
                .filter(s => newState[s.paragraphLetter] && newState[s.paragraphLetter] !== "")
                .map(s => s.questionNumber);
            markAnswered(answered);
            return newState;
        });
    };

    const handleDragStartHeading = (e: React.DragEvent, headingId: string) => {
        e.dataTransfer.setData("text/plain", headingId);
        e.dataTransfer.effectAllowed = "move";
    };

    const renderQuestionGroup = (group: any, idx: number) => {
        const rangeStart = group.range[0];
        const rangeEnd = group.range[1];
        const groupType = group.type || "";

        const instructionBar = (
            <div
                style={{
                    backgroundColor: "var(--ielts-instruction-bar-bg)", // F5F5F5
                    padding: "16px 24px",
                    borderBottom: "1px solid var(--ielts-border-default)",
                    fontFamily: "var(--ielts-font)",
                }}
            >
                <div
                    style={{
                        fontWeight: 700,
                        fontSize: "16px",
                        color: "#333",
                        marginBottom: group.instructions ? "6px" : "0",
                    }}
                >
                    Questions {rangeStart} – {rangeEnd}
                </div>
                {group.instructions && (
                    <p
                        style={{
                            fontSize: "14px",
                            color: "#555",
                            lineHeight: 1.5,
                            fontStyle: "italic",
                        }}
                    >
                        {group.instructions}
                    </p>
                )}
            </div>
        );

        if (groupType === "MATCHING_HEADINGS") {
            const assignedHeadingIds = Object.values(headingAssignments).filter(Boolean);
            const availableHeadings = headingsBank.filter(h => !assignedHeadingIds.includes(h.id));

            const handleDropOnBank = (e: React.DragEvent) => {
                e.preventDefault();
                const headingId = e.dataTransfer.getData("text/plain");
                if (!headingId) return;

                setHeadingAssignments(prev => {
                    const newState = { ...prev };
                    for (const key in newState) {
                        if (newState[key] === headingId) {
                            newState[key] = "";
                        }
                    }
                    return newState;
                });
            };

            return (
                <section
                    key={idx}
                    className="mb-10 overflow-hidden"
                    style={{ border: "1px solid var(--ielts-border-default)", borderRadius: "2px" }}
                >
                    {instructionBar}
                    <div
                        onDragOver={handleDragOver}
                        onDrop={handleDropOnBank}
                        style={{
                            padding: "24px 32px",
                            backgroundColor: "#fff",
                            minHeight: "100px",
                            borderBottom: "1px solid var(--ielts-border-default)",
                        }}
                    >
                        <p
                            style={{
                                fontSize: "14px",
                                fontWeight: 700,
                                color: "#666",
                                marginBottom: "16px",
                                textTransform: "uppercase",
                                letterSpacing: "0.03em",
                            }}
                        >
                            List of Headings
                        </p>
                        <div className="flex flex-col items-start gap-[15px]">
                            {availableHeadings.map((h) => (
                                <div
                                    key={h.id}
                                    draggable
                                    onDragStart={(e) => handleDragStartHeading(e, h.id)}
                                    className="flex items-center gap-2 cursor-grab active:cursor-grabbing hover:shadow-md transition-shadow"
                                    style={{
                                        backgroundColor: "#fff",
                                        border: "1px solid #c8c8c8",
                                        borderRadius: "4px",
                                        padding: "8px 14px",
                                        position: "relative",
                                        zIndex: 1,
                                        fontSize: "14px",
                                        color: "#333",
                                        maxWidth: "100%",
                                    }}
                                >
                                    <span style={{ lineHeight: 1.3 }}>{h.text}</span>
                                </div>
                            ))}
                            {availableHeadings.length === 0 && (
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
                                    All headings assigned. Drag back to return.
                                </div>
                            )}
                        </div>
                    </div>
                </section >
            );
        }

        if (groupType === "MATCHING_PARAGRAPH_INFORMATION" || groupType === "MATCHING_INFORMATION") {
            const matrixQuestions = group.questions.map((q: any) => ({
                questionNumber: q.number,
                text: q.text || "",
            }));

            const paragraphLetters = (itemData?.passage?.paragraphs || [])
                .map((p: any) => p.label)
                .filter((l: string) => l && l.trim());

            return (
                <section
                    key={idx}
                    className="mb-10 overflow-hidden"
                    style={{ border: "1px solid var(--ielts-border-default)", borderRadius: "2px" }}
                >
                    {instructionBar}
                    <div style={{ padding: "24px 32px", backgroundColor: "#fff" }}>
                        <MatchingMatrix
                            questions={matrixQuestions}
                            paragraphLetters={paragraphLetters}
                            onAnswerChange={(answers) => {
                                const answered = Object.entries(answers)
                                    .filter(([, v]) => v && v !== "")
                                    .map(([k]) => Number(k));
                                markAnswered(answered);
                            }}
                        />
                    </div>
                </section>
            );
        }

        return (
            <section
                key={idx}
                className="mb-10 overflow-hidden"
                style={{ border: "1px solid var(--ielts-border-default)", borderRadius: "2px" }}
            >
                {instructionBar}
                <div style={{ backgroundColor: "#fff", padding: "8px 0" }}>
                    {group.questions?.map((q: any) => renderQuestion(q, groupType))}
                </div>
            </section>
        );
    };

    const renderQuestion = (q: any, groupType: string) => {
        const qNum = q.number;

        const standardTFNG = new Set(["TRUE", "FALSE", "NOT GIVEN", "YES", "NO"]);
        const hasRealMCQOptions = q.options && q.options.length > 0
            && (groupType === "TRUE_FALSE_NOT_GIVEN" || groupType === "YES_NO_NOT_GIVEN")
            && !q.options.every((opt: any) => standardTFNG.has((opt.label || opt.text || "").toUpperCase()));

        if (hasRealMCQOptions) {
            const options = q.options.map((opt: any, oidx: number) => ({
                letter: opt.label || opt.letter || String.fromCharCode(65 + oidx),
                text: opt.text || "",
            }));

            return (
                <div key={qNum}>
                    <MultipleChoiceQuestion
                        questionNumber={qNum}
                        text={q.text}
                        options={options}
                        multi={true}
                        onAnswerChange={(ans) => {
                            if (ans && (Array.isArray(ans) ? ans.length > 0 : true)) {
                                markAnswered([qNum]);
                            }
                        }}
                    />
                </div>
            );
        }

        if (groupType === "TRUE_FALSE_NOT_GIVEN") {
            return (
                <div key={qNum}>
                    <TrueFalseNotGiven
                        questionNumber={qNum}
                        questionText={q.text}
                        type="TFNG"
                        onAnswerChange={(ans) => {
                            if (ans) markAnswered([qNum]);
                        }}
                    />
                </div>
            );
        }

        if (groupType === "YES_NO_NOT_GIVEN") {
            return (
                <div key={qNum}>
                    <TrueFalseNotGiven
                        questionNumber={qNum}
                        questionText={q.text}
                        type="YNNG"
                        onAnswerChange={(ans) => {
                            if (ans) markAnswered([qNum]);
                        }}
                    />
                </div>
            );
        }

        if (groupType === "MULTIPLE_CHOICE" || groupType === "MULTIPLE_CHOICE_M") {
            const options = (q.options || []).map((opt: any, oidx: number) => ({
                letter: opt.label || opt.letter || String.fromCharCode(65 + oidx),
                text: opt.text || "",
            }));

            return (
                <div key={qNum}>
                    <MultipleChoiceQuestion
                        questionNumber={qNum}
                        text={q.text}
                        options={options}
                        multi={groupType === "MULTIPLE_CHOICE_M"}
                        onAnswerChange={(ans) => {
                            if (ans && (Array.isArray(ans) ? ans.length > 0 : true)) {
                                markAnswered([qNum]);
                            }
                        }}
                    />
                </div>
            );
        }

        if (groupType === "MATCHING_FEATURES" || groupType === "CLASSIFICATION" || groupType === "MATCHING_SENTENCE_ENDINGS") {
            const options = (q.options || []).map((opt: any) => ({
                id: opt.label || opt.letter || opt.id,
                text: opt.text || "",
            }));

            return (
                <div key={qNum}>
                    <MatchingItem
                        questionNumber={qNum}
                        promptText={q.text}
                        options={options}
                        showOptionsGrid={options.length > 0}
                        onAnswerChange={(ans) => {
                            if (ans) markAnswered([qNum]);
                        }}
                    />
                </div>
            );
        }

        if (
            groupType === "SUMMARY_COMPLETION" ||
            groupType === "SENTENCE_COMPLETION" ||
            groupType === "TABLE_COMPLETION" ||
            groupType === "FLOW_CHART_COMPLETION" ||
            groupType === "DIAGRAM_LABEL_COMPLETION" ||
            groupType === "LABEL_DIAGRAM"
        ) {
            return (
                <div key={qNum}>
                    <GapFillItem
                        questionNumber={qNum}
                        contentHtml={q.text || ""}
                        onAnswerChange={(ans) => {
                            if (ans && ans.trim()) markAnswered([qNum]);
                        }}
                    />
                </div>
            );
        }

        return (
            <div key={qNum}>
                <ShortAnswerQuestion
                    questionNumber={qNum}
                    text={q.text}
                />
            </div>
        );
    };

    const leftContent = itemData ? (
        <TextMarkupEngine>
            <div className="flex flex-col gap-0" style={{ fontFamily: "var(--ielts-font)" }}>
                <h1
                    style={{
                        fontSize: "22px",
                        fontWeight: 700,
                        marginBottom: "20px",
                        color: "#333",
                        fontFamily: "var(--ielts-font)",
                    }}
                >
                    {itemData.title}
                </h1>
                {itemData.passage?.paragraphs?.map((p: any, i: number) => {
                    const slot = headingSlots.find(s => s.paragraphLetter === p.label);
                    const assignedId = slot ? headingAssignments[p.label] : null;
                    const assignedHeading = assignedId ? headingsBank.find(h => h.id === assignedId) : null;

                    return (
                        <div key={i} className="mb-3">
                            {slot && (
                                <div
                                    data-question-id={slot.questionNumber}
                                    onDragOver={handleDragOver}
                                    onDrop={(e) => handleDropOnPassageZone(e, p.label)}
                                    className="flex items-center gap-2 mb-1"
                                    style={{
                                        minHeight: "32px",
                                        padding: "4px 10px",
                                        border: assignedHeading
                                            ? "1px solid var(--ielts-active-blue)"
                                            : "1px dashed var(--ielts-drop-zone-border)",
                                        borderRadius: "2px",
                                        backgroundColor: assignedHeading ? "rgba(65, 143, 198, 0.06)" : "#fff",
                                        transition: "border-color 0.15s, background-color 0.15s",
                                        maxWidth: "40%",
                                        marginLeft: itemData.passage.has_paragraph_labels && p.label ? "38px" : "0",
                                    }}
                                >
                                    <span
                                        style={{
                                            fontWeight: 700,
                                            fontSize: "13px",
                                            color: assignedHeading ? "var(--ielts-active-blue)" : "#999",
                                            minWidth: "20px",
                                        }}
                                    >
                                        {slot.questionNumber}
                                    </span>
                                    {assignedHeading ? (
                                        <div
                                            draggable
                                            onDragStart={(e) => handleDragStartHeading(e, assignedHeading.id)}
                                            className="flex items-center gap-2 cursor-grab active:cursor-grabbing"
                                            style={{ fontSize: "14px", color: "#333" }}
                                        >
                                            <span style={{ fontWeight: 700 }}>{assignedHeading.id}</span>
                                            <span>{assignedHeading.text}</span>
                                        </div>
                                    ) : (
                                        <span style={{ fontSize: "13px", color: "#bbb", fontStyle: "italic" }}>
                                            Drag heading here
                                        </span>
                                    )}
                                </div>
                            )}

                            <div className="flex">
                                {itemData.passage.has_paragraph_labels && p.label && (
                                    <div
                                        style={{
                                            fontWeight: 700,
                                            fontSize: "16px",
                                            width: "24px",
                                            flexShrink: 0,
                                            paddingTop: "2px",
                                            marginRight: "8px",
                                            color: "#333",
                                            textAlign: "right",
                                            paddingRight: "6px",
                                            lineHeight: 1.6,
                                        }}
                                    >
                                        {p.label}
                                    </div>
                                )}
                                <p
                                    style={{
                                        color: "#333",
                                        flex: 1,
                                        whiteSpace: "pre-wrap",
                                        maxWidth: "85ch",
                                        lineHeight: 1.6,
                                        fontSize: "16px",
                                    }}
                                >
                                    {p.text}
                                </p>
                            </div>
                        </div>
                    );
                })}
            </div>
        </TextMarkupEngine>
    ) : null;

    const rightContent = itemData ? (
        <div className="flex flex-col gap-0 pb-20">
            {itemData.question_groups?.map((group: any, idx: number) => renderQuestionGroup(group, idx))}

            <div
                className="flex flex-col items-center justify-center mt-6"
                style={{
                    height: "80px",
                    border: "1px dashed var(--ielts-border-default)",
                    backgroundColor: "#fafafa",
                    borderRadius: "4px",
                }}
            >
                <span style={{ fontWeight: 500, fontSize: "15px", color: "#999" }}>
                    End of Questions
                </span>
                <span style={{ fontSize: "13px", color: "#bbb" }}>
                    Please check your answers
                </span>
            </div>
        </div>
    ) : null;

    return (
        <div className="flex flex-col h-screen w-screen overflow-hidden bg-white antialiased">
            {/* Dashboard Control Header */}
            <div
                id="dashboard-header"
                className="bg-[#1e293b] text-white p-3 flex items-center justify-between border-b border-gray-700 select-none z-50 flex-shrink-0"
                style={{ fontFamily: 'var(--ielts-font)' }}
            >
                <div className="flex items-center gap-4">
                    <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-teal-400 bg-clip-text text-transparent">
                        IELTS Item QA Dashboard
                    </h1>
                    <div className="flex items-center gap-2 bg-[#0f172a] px-3 py-1.5 rounded-md border border-gray-600">
                        <label htmlFor="item-select" className="text-sm text-gray-400 uppercase tracking-wider font-semibold">Select Item:</label>
                        <select
                            id="item-select"
                            value={selectedItemId}
                            onChange={(e) => setSelectedItemId(e.target.value)}
                            className="bg-transparent text-white text-sm outline-none border-none py-1 min-w-[300px] cursor-pointer"
                        >
                            {itemsList.map(item => (
                                <option key={item.id} value={item.id} className="bg-[#1e293b] text-white">
                                    [{item.id}] {item.title || "Untitled"} ({item.questionCount} Qs)
                                </option>
                            ))}
                        </select>
                    </div>
                </div>

                {itemData && itemData._meta && (
                    <div className="flex items-center gap-3 text-xs bg-[#0f172a] px-3 py-2 rounded-md border border-gray-600 shadow-inner">
                        <div className="flex flex-col">
                            <span className="text-gray-400 font-medium uppercase tracking-widest text-[10px] mb-0.5">Types</span>
                            <div className="flex gap-1">
                                {(itemData._meta.question_types || []).map((t: string) => (
                                    <span key={t} className="bg-blue-900/40 text-blue-300 px-1.5 py-0.5 rounded outline outline-1 outline-blue-800 border-none inline-block">
                                        {t.replace(/_/g, " ")}
                                    </span>
                                ))}
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Main IELTS Interface Window */}
            {loading ? (
                <div className="flex-1 flex flex-col items-center justify-center bg-[#f4f4f4]">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4"></div>
                    <div className="text-gray-500 font-mono text-sm uppercase tracking-widest">Loading Item Database...</div>
                </div>
            ) : error ? (
                <div className="flex-1 flex items-center justify-center bg-[#f4f4f4] text-red-600 font-semibold shadow-inner">
                    <div className="bg-red-50 px-8 py-6 rounded-lg border border-red-200">
                        <h2 className="text-xl mb-2 text-red-800">Cannot Load Interface</h2>
                        <p className="text-red-600 text-sm">{error}</p>
                    </div>
                </div>
            ) : (
                <div className="flex flex-col flex-1 h-full w-full relative shadow-[inset_0_4px_10px_rgba(0,0,0,0.15)] ring-1 ring-inset ring-black/5 bg-[#f4f4f4]">
                    <IELTSHeader onTimeExpired={handleTimeExpired} />

                    <SplitPane
                        leftContent={leftContent}
                        rightContent={rightContent}
                        leftScrollTop={leftScrollTop}
                        rightScrollTop={rightScrollTop}
                        onLeftScroll={setLeftScrollTop}
                        onRightScroll={setRightScrollTop}
                        colorScheme={colorScheme}
                        textSize={textSize}
                        rightPaneRef={rightPaneRef}
                        leftPaneRef={leftPaneRef}
                    />

                    <FooterNavigation
                        questions={questions}
                        currentQuestionId={currentQuestionId}
                        onQuestionClick={handleQuestionClick}
                        onReviewToggle={handleReviewToggle}
                        onSettingsClick={() => { }}
                    />
                </div>
            )}
        </div>
    );
}
