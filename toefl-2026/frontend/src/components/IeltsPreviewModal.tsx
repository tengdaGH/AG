import React, { useEffect, useState } from 'react';
import { Button } from '@/components/Button';
import QuestionBlock from "@/components/ielts/questions/QuestionBlock";
import MultipleChoiceItem from "@/components/ielts/questions/MultipleChoiceItem";
import MatchingItem from "@/components/ielts/questions/MatchingItem";
import GapFillItem from "@/components/ielts/questions/GapFillItem";

interface IeltsPreviewModalProps {
    passageId: string | null;
    onClose: () => void;
}

export const IeltsPreviewModal: React.FC<IeltsPreviewModalProps> = ({ passageId, onClose }) => {
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!passageId) return;

        const fetchData = async () => {
            setLoading(true);
            setError(null);
            try {
                const res = await fetch(`http://localhost:8000/api/ielts/readings/${passageId}`);
                if (!res.ok) {
                    throw new Error('Failed to fetch passage data');
                }
                const jsonData = await res.json();
                setData(jsonData);
            } catch (err: any) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [passageId]);

    const renderQuestion = (q: any, groupType: string) => {
        const isMCQ = groupType.includes("MULTIPLE_CHOICE");
        const isTFNG = groupType === "TRUE_FALSE_NOT_GIVEN";
        const isYNNG = groupType === "YES_NO_NOT_GIVEN";
        const isMatching = groupType.includes("MATCHING");

        const answerPill = (
            <div style={{ marginTop: '1rem', marginLeft: '5rem', marginBottom: '1.5rem', display: 'inline-block', padding: '0.25rem 0.75rem', backgroundColor: 'rgba(22, 163, 74, 0.1)', color: '#16a34a', borderRadius: '9999px', fontSize: '0.875rem', fontWeight: 600 }}>
                Answer: {q.answer || "N/A"}
            </div>
        );

        if (isMCQ || isTFNG || isYNNG) {
            let options = [];
            if (isTFNG) {
                options = [{ id: "TRUE" }, { id: "FALSE" }, { id: "NOT GIVEN" }];
            } else if (isYNNG) {
                options = [{ id: "YES" }, { id: "NO" }, { id: "NOT GIVEN" }];
            } else if (q.options) {
                options = q.options.map((opt: any, idx: number) => {
                    const isDict = typeof opt === 'object' && opt !== null;
                    const letter = isDict ? opt.letter : String.fromCharCode(65 + idx);
                    const text = isDict ? opt.text : opt;
                    return { id: letter, text: text };
                });
            }

            return (
                <div key={q.id || q.number || q.question_number} className="group">
                    <MultipleChoiceItem
                        questionNumber={q.question_number || q.number}
                        text={<span dangerouslySetInnerHTML={{ __html: q.question_text || q.text || "" }} />}
                        options={options}
                        multi={groupType === "MULTIPLE_CHOICE_M"}
                    />
                    {answerPill}
                </div>
            );
        }

        if (isMatching) {
            return (
                <div key={q.id || q.number || q.question_number} className="group">
                    <MatchingItem
                        questionNumber={q.question_number || q.number}
                        promptText={<span dangerouslySetInnerHTML={{ __html: q.question_text || q.text || "" }} />}
                        options={[]}
                    />
                    {answerPill}
                </div>
            );
        }

        return (
            <div key={q.id || q.number || q.question_number} className="group">
                <GapFillItem
                    questionNumber={q.question_number || q.number}
                    contentHtml={q.question_text || q.text || ""}
                />
                {answerPill}
            </div>
        );
    };

    if (!passageId) return null;

    return (
        <div style={{
            position: 'fixed',
            top: 0, left: 0, right: 0, bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            zIndex: 9999,
            display: 'flex',
            flexDirection: 'column',
            padding: '2rem'
        }}>
            <div style={{
                backgroundColor: 'var(--background)',
                borderRadius: '12px',
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden',
                boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)'
            }}>
                {/* Header */}
                <div style={{
                    padding: '1rem 1.5rem',
                    borderBottom: '1px solid var(--border-color)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    backgroundColor: 'var(--card-bg)'
                }}>
                    <div>
                        <span style={{ fontFamily: 'var(--font-heading)', fontWeight: 600, fontSize: '1.25rem' }}>
                            CD-IELTS Preview: {data?.title || passageId}
                        </span>
                        {data && (
                            <span style={{ marginLeft: '1rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                                {data.position?.replace('P', 'Passage ')} &bull; {data.difficulty ? data.difficulty.charAt(0) + data.difficulty.slice(1).toLowerCase() : 'Unknown'}
                            </span>
                        )}
                    </div>
                    <Button variant="ghost" onClick={onClose}>Close Preview</Button>
                </div>

                {/* Content Area - Split Pane */}
                {loading ? (
                    <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <span style={{ color: 'var(--text-muted)' }}>Loading authentic preview...</span>
                    </div>
                ) : error ? (
                    <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ef4444' }}>
                        Error: {error}
                    </div>
                ) : data ? (
                    <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>

                        {/* Left Pane: Reading Passage */}
                        <div style={{
                            flex: 1,
                            borderRight: '1px solid var(--border-color)',
                            overflowY: 'auto',
                            padding: '2rem 3rem',
                            backgroundColor: 'white'
                        }}>
                            <h1 style={{ fontFamily: 'var(--font-heading)', fontSize: '2rem', marginBottom: '2rem', textAlign: 'center' }}>
                                {data.title}
                            </h1>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', fontFamily: 'var(--font-body)', fontSize: '1.1rem', lineHeight: 1.6 }}>
                                {data.paragraphs.map((p: any, idx: number) => (
                                    <div key={idx} style={{ display: 'flex' }}>
                                        {data.has_paragraph_labels && (
                                            <div style={{ width: '40px', fontWeight: 'bold', paddingTop: '2px' }}>{p.label}</div>
                                        )}
                                        <div style={{ flex: 1 }}>{p.text}</div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Right Pane: Questions */}
                        <div style={{
                            flex: 1,
                            overflowY: 'auto',
                            padding: '2rem 3rem',
                            backgroundColor: '#F5F7FA'
                        }}>
                            {data.question_groups.map((group: any, gIdx: number) => {
                                const qNums = group.questions.map((q: any) => q.question_number || q.number).filter(Boolean);
                                const qRange = qNums.length > 1 ? `Questions ${qNums[0]}-${qNums[qNums.length - 1]}` : (qNums.length === 1 ? `Question ${qNums[0]}` : undefined);

                                return (
                                    <QuestionBlock
                                        key={group.id || gIdx}
                                        instructions={
                                            <div>
                                                <span style={{ fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                                                    {group.group_type?.replace(/_/g, ' ')}
                                                </span>
                                                {group.instructions && (
                                                    <span dangerouslySetInnerHTML={{ __html: group.instructions }} />
                                                )}
                                            </div>
                                        }
                                        questionRange={qRange}
                                    >
                                        {group.questions.map((q: any) => renderQuestion(q, group.group_type || group.type))}
                                    </QuestionBlock>
                                );
                            })}
                        </div>
                    </div>
                ) : null}
            </div>
        </div>
    );
};
