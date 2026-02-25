'use client';

import React, { useState, useEffect } from 'react';
import { DndContext, useSensor, useSensors, PointerSensor, DragEndEvent, DragOverlay, closestCenter } from '@dnd-kit/core';
import { useDraggable, useDroppable, useDndContext } from '@dnd-kit/core';

interface BuildSentenceProps {
    contextSpeakerUrl: string;
    contextText: string;
    builderSpeakerUrl: string;
    prefixText: string;
    suffixText: string;
    scrambledWords: string[];
    onSentenceUpdate?: (currentOrder: string[]) => void;
}

// Subcomponents for DnD
const DraggableWord = ({ id, word, isDragging }: { id: string, word: string, isDragging?: boolean }) => {
    const { attributes, listeners, setNodeRef, transform } = useDraggable({
        id: id,
        data: { word }
    });

    const [isHovered, setIsHovered] = useState(false);

    const style: React.CSSProperties = {
        transform: transform ? `translate3d(${transform.x}px, ${transform.y}px, 0)` : undefined,
        padding: '2px 8px',
        backgroundColor: isHovered ? '#F0F8F8' : 'transparent',
        borderRadius: '2px',
        cursor: isDragging ? 'grabbing' : 'grab',
        opacity: isDragging ? 0.4 : 1,
        fontSize: '18px',
        fontFamily: 'Times New Roman, Times, serif',
        color: '#212121',
        display: 'inline-block',
        touchAction: 'none',
        lineHeight: '1.2',
        transition: 'all 0.2s ease'
    };

    return (
        <div
            ref={setNodeRef}
            style={style}
            {...listeners}
            {...attributes}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
        >
            {word}
        </div>
    );
};

const DroppableSlot = ({ id, currentWordObj }: { id: string, currentWordObj: { id: string, word: string } | null }) => {
    const { isOver, setNodeRef } = useDroppable({
        id: id
    });
    const { active } = useDndContext();
    const isDragging = active !== null;

    return (
        <div
            ref={setNodeRef}
            style={{
                minWidth: currentWordObj ? 'auto' : '80px',
                borderBottom: isOver ? '2px solid #008080' : (isDragging && !currentWordObj ? '2px dashed #008080' : '1px solid #767676'),
                display: 'inline-block',
                verticalAlign: 'baseline',
                textAlign: 'center',
                margin: '0 5px',
                backgroundColor: isOver ? 'rgba(0, 128, 128, 0.2)' : (isDragging && !currentWordObj ? 'rgba(0, 128, 128, 0.05)' : 'transparent'),
                transition: 'all 0.2s ease',
                borderRadius: '2px 2px 0 0'
            }}
        >
            {currentWordObj ? (
                <DraggableWord id={currentWordObj.id} word={currentWordObj.word} />
            ) : (
                <div style={{
                    padding: '2px 8px',
                    fontSize: '18px',
                    fontFamily: 'Times New Roman, Times, serif',
                    lineHeight: '1.2',
                    visibility: 'hidden',
                    display: 'inline-block'
                }}>
                    X
                </div>
            )}
        </div>
    );
};

const DroppableBank = ({ children }: { children: React.ReactNode }) => {
    const { isOver, setNodeRef } = useDroppable({
        id: 'word-bank'
    });
    const { active } = useDndContext();
    const isDragging = active !== null;

    return (
        <div
            ref={setNodeRef}
            style={{
                display: 'flex',
                gap: '20px',
                justifyContent: 'center',
                flexWrap: 'wrap',
                minHeight: '60px',
                alignItems: 'center',
                padding: '10px',
                backgroundColor: isOver ? 'rgba(0, 128, 128, 0.05)' : (isDragging ? 'rgba(0,0,0,0.02)' : 'transparent'),
                border: isDragging ? '1px dashed #CCCCCC' : '1px solid transparent',
                borderRadius: '8px',
                transition: 'all 0.2s ease'
            }}
        >
            {children}
        </div>
    );
};

export const BuildSentence: React.FC<BuildSentenceProps> = ({
    contextSpeakerUrl,
    contextText,
    builderSpeakerUrl,
    prefixText,
    suffixText,
    scrambledWords,
    onSentenceUpdate
}) => {
    // Array of words currently in the bank
    const [wordBank, setWordBank] = useState<{ id: string, word: string }[]>([]);

    // Array of slots (length = number of words)
    // Each slot either holds a word object or is null
    const [slots, setSlots] = useState<({ id: string, word: string } | null)[]>([]);

    useEffect(() => {
        setWordBank(scrambledWords.map((word, idx) => ({ id: `word-${idx}`, word })));
        setSlots(new Array(scrambledWords.length).fill(null));
    }, [JSON.stringify(scrambledWords)]);

    const sensors = useSensors(
        useSensor(PointerSensor, {
            activationConstraint: {
                distance: 5,
            },
        })
    );

    const [activeId, setActiveId] = useState<string | null>(null);
    const [activeWord, setActiveWord] = useState<string | null>(null);

    const handleDragStart = (event: any) => {
        setActiveId(event.active.id);
        setActiveWord(event.active.data.current?.word || null);
    };

    const handleDragEnd = (event: DragEndEvent) => {
        setActiveId(null);
        setActiveWord(null);

        const { active, over } = event;
        if (!over) return;

        const activeIdStr = active.id as string;
        const overId = over.id as string;

        const isFromBank = wordBank.some(w => w.id === activeIdStr);
        let sourceIndex = -1;

        if (isFromBank) {
            sourceIndex = wordBank.findIndex(w => w.id === activeIdStr);
        } else {
            sourceIndex = slots.findIndex(s => s && s.id === activeIdStr);
        }

        if (sourceIndex === -1) return;

        const sourceItem = isFromBank ? wordBank[sourceIndex] : slots[sourceIndex]!;

        if (overId === 'word-bank') {
            if (!isFromBank) {
                const newSlots = [...slots];
                newSlots[sourceIndex] = null;
                setSlots(newSlots);

                setWordBank([...wordBank, sourceItem]);
                if (onSentenceUpdate) {
                    onSentenceUpdate(newSlots.filter(s => s !== null).map(s => s!.word));
                }
            }
        } else if (overId.startsWith('slot-')) {
            const targetIndex = parseInt(overId.replace('slot-', ''), 10);
            const newSlots = [...slots];
            const newBank = [...wordBank];
            const targetItem = newSlots[targetIndex];

            if (isFromBank) {
                newBank.splice(sourceIndex, 1);
                // If target slot has a word, push it back to bank
                if (targetItem) {
                    newBank.push(targetItem);
                }
                newSlots[targetIndex] = sourceItem;
            } else {
                // Insert behavior: remove from source, insert at target, shift others
                newSlots[sourceIndex] = null;
                // Collect all non-null words in order, excluding the dragged item
                const occupied: { slot: number, item: { id: string, word: string } }[] = [];
                for (let i = 0; i < newSlots.length; i++) {
                    if (newSlots[i] && newSlots[i]!.id !== sourceItem.id) {
                        occupied.push({ slot: i, item: newSlots[i]! });
                    }
                }
                // Determine insertion position in the occupied list
                let insertIdx = occupied.findIndex(o => o.slot >= targetIndex);
                if (insertIdx === -1) insertIdx = occupied.length;
                // Insert the dragged item at the determined position
                occupied.splice(insertIdx, 0, { slot: targetIndex, item: sourceItem });
                // Clear all slots and re-fill from left
                for (let i = 0; i < newSlots.length; i++) newSlots[i] = null;
                for (let i = 0; i < occupied.length; i++) {
                    newSlots[i] = occupied[i].item;
                }
            }

            setSlots(newSlots);
            setWordBank(newBank);
            if (onSentenceUpdate) {
                onSentenceUpdate(newSlots.filter(s => s !== null).map(s => s!.word));
            }
        }
    };

    return (
        <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
        >
            <div style={{ padding: '40px', maxWidth: '1000px', margin: '0 auto', fontFamily: 'Times New Roman, Times, serif', color: '#212121', backgroundColor: '#FFFFFF', minHeight: '600px' }}>
                <h2 style={{ color: '#008080', textAlign: 'center', fontSize: '24px', fontWeight: 'bold', marginBottom: '80px' }}>
                    Make an appropriate sentence.
                </h2>

                {/* Context Row */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '20px', marginBottom: '80px', paddingLeft: '80px' }}>
                    <img
                        src={contextSpeakerUrl}
                        alt="Context Speaker"
                        style={{ width: '80px', height: '80px', borderRadius: '50%', border: '2px solid #008080', objectFit: 'cover' }}
                    />
                    <span style={{ fontSize: '18px' }}>{contextText}</span>
                </div>

                {/* Word Bank */}
                <div style={{ paddingLeft: '80px', paddingRight: '40px', marginBottom: '60px' }}>
                    <DroppableBank>
                        {wordBank.map((item) => (
                            <DraggableWord key={item.id} id={item.id} word={item.word} />
                        ))}
                    </DroppableBank>
                </div>

                {/* Sentence Row */}
                <div style={{ display: 'flex', alignItems: 'flex-end', gap: '20px', paddingLeft: '80px' }}>
                    <img
                        src={builderSpeakerUrl}
                        alt="Builder Speaker"
                        style={{ width: '80px', height: '80px', borderRadius: '50%', border: '2px solid #008080', objectFit: 'cover', flexShrink: 0 }}
                    />
                    <div style={{ display: 'flex', alignItems: 'baseline', fontSize: '18px', paddingBottom: '0px', flexWrap: 'wrap', gap: '4px', lineHeight: '1.2' }}>
                        <span>{prefixText}</span>
                        {slots.map((item, idx) => (
                            <DroppableSlot key={`slot-${idx}`} id={`slot-${idx}`} currentWordObj={item} />
                        ))}
                        <span>{suffixText}</span>
                    </div>
                </div>
            </div>

            <DragOverlay>
                {activeId ? (
                    <div style={{
                        padding: '2px 8px',
                        backgroundColor: '#FFFFFF',
                        borderRadius: '2px',
                        fontSize: '18px',
                        fontFamily: 'Times New Roman, Times, serif',
                        color: '#212121',
                        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                        opacity: 0.9,
                        lineHeight: '1.2'
                    }}>
                        {activeWord}
                    </div>
                ) : null}
            </DragOverlay>
        </DndContext>
    );
};

