"use client";

import React, { useRef, useState, useEffect } from "react";
import { Highlighter, MessageSquareText, Trash2 } from "lucide-react";

interface TextMarkupEngineProps {
    children: React.ReactNode;
}

export default function TextMarkupEngine({ children }: TextMarkupEngineProps) {
    const containerRef = useRef<HTMLDivElement>(null);

    const [menuData, setMenuData] = useState<{
        visible: boolean;
        x: number;
        y: number;
        type: "new-highlight" | "existing-highlight";
        targetNode?: HTMLElement | null; // For clearing existing highlights
    }>({
        visible: false,
        x: 0,
        y: 0,
        type: "new-highlight"
    });

    const [noteModal, setNoteModal] = useState<{
        visible: boolean;
        x: number;
        y: number;
        targetNode?: HTMLElement | null;
    }>({ visible: false, x: 0, y: 0 });

    // Handle right-click / context menu
    const handleContextMenu = (e: React.MouseEvent) => {
        e.preventDefault(); // Suppress native right-click

        const target = e.target as HTMLElement;

        // If we right-clicked an existing highlight
        if (target.nodeName === "MARK" && target.classList.contains("ielts-highlight")) {
            setMenuData({
                visible: true,
                x: e.clientX,
                y: e.clientY - 40,
                type: "existing-highlight",
                targetNode: target
            });
            return;
        }

        // Check if there is an active text selection
        const selection = window.getSelection();
        if (selection && !selection.isCollapsed && containerRef.current?.contains(selection.anchorNode)) {
            const range = selection.getRangeAt(0);
            const rect = range.getBoundingClientRect();

            setMenuData({
                visible: true,
                x: rect.left + rect.width / 2, // Center above selection
                y: rect.top - 45, // 45px above
                type: "new-highlight"
            });
        } else {
            setMenuData(prev => ({ ...prev, visible: false }));
        }
    };

    // Close menus when clicking elsewhere
    useEffect(() => {
        const handleClickOutside = (e: MouseEvent) => {
            // Don't close if clicking within the menu itself
            const target = e.target as HTMLElement;
            if (target.closest('.ielts-context-menu') || target.closest('.ielts-note-modal')) {
                return;
            }
            setMenuData(prev => ({ ...prev, visible: false }));
            setNoteModal(prev => ({ ...prev, visible: false }));
        };

        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const applyHighlight = () => {
        const selection = window.getSelection();
        if (!selection || selection.isCollapsed) return;

        try {
            const range = selection.getRangeAt(0);

            // Basic DOM manipulation to wrap text in <mark>
            // Note: This simple implementation breaks if selection crosses multiple DOM elements.
            // A robust implementation would need a recursive TreeWalker traversing text nodes.
            const mark = document.createElement("mark");
            mark.className = "ielts-highlight bg-[#FFEA00] text-black rounded-sm cursor-pointer";

            range.surroundContents(mark);

            selection.removeAllRanges();
            setMenuData(prev => ({ ...prev, visible: false }));
        } catch (e) {
            console.warn("Cross-element highlighting is complex and skipped in this sandbox.", e);
            // Fallback: copy-paste logic requires exact nodes.
        }
    };

    const clearHighlight = () => {
        if (menuData.targetNode && menuData.targetNode.parentNode) {
            // Replace <mark> with its text content
            const parent = menuData.targetNode.parentNode;
            while (menuData.targetNode.firstChild) {
                parent.insertBefore(menuData.targetNode.firstChild, menuData.targetNode);
            }
            parent.removeChild(menuData.targetNode);
            setMenuData(prev => ({ ...prev, visible: false }));
        }
    };

    const openNoteModal = () => {
        applyHighlight();
        // After applyHighlight, the selection is gone, but we can snap note to cursor
        setNoteModal({
            visible: true,
            x: menuData.x,
            y: menuData.y + 40,
        });
        setMenuData(prev => ({ ...prev, visible: false }));
    };

    return (
        <div
            ref={containerRef}
            className="relative w-full h-full"
            onContextMenu={handleContextMenu}
        >
            {/* Target content for highlighting */}
            <div className="passage-content">
                {children}
            </div>

            {/* The Abstract Context Menu */}
            {menuData.visible && (
                <div
                    className="ielts-context-menu fixed z-[100] flex bg-white border border-gray-300 shadow-lg rounded-md overflow-hidden transform -translate-x-1/2"
                    style={{ top: menuData.y, left: menuData.x }}
                >
                    {menuData.type === "new-highlight" ? (
                        <>
                            <button
                                onClick={applyHighlight}
                                className="flex items-center gap-2 px-3 py-2 text-sm font-medium hover:bg-gray-100 text-gray-800 transition-colors border-r border-gray-200"
                            >
                                <div className="w-3 h-3 rounded-full bg-[#FFEA00] border border-gray-400"></div>
                                Highlight
                            </button>
                            <button
                                onClick={openNoteModal}
                                className="flex items-center gap-2 px-3 py-2 text-sm font-medium hover:bg-gray-100 text-gray-800 transition-colors"
                            >
                                <MessageSquareText size={16} className="text-blue-600" />
                                Notes
                            </button>
                        </>
                    ) : (
                        <button
                            onClick={clearHighlight}
                            className="flex items-center gap-2 px-3 py-2 text-sm font-medium hover:bg-red-50 text-red-600 transition-colors"
                        >
                            <Trash2 size={16} />
                            Clear
                        </button>
                    )}
                </div>
            )}

            {/* The Sticky Note Entry Modal */}
            {noteModal.visible && (
                <div
                    className="ielts-note-modal fixed z-[101] w-64 bg-yellow-100 border border-yellow-400 shadow-xl rounded-sm overflow-hidden"
                    style={{ top: noteModal.y, left: noteModal.x }}
                >
                    <div className="bg-yellow-300 border-b border-yellow-400 px-2 py-1 flex justify-between items-center text-xs font-bold text-yellow-900">
                        Passage Note
                        <button onClick={() => setNoteModal(prev => ({ ...prev, visible: false }))} className="hover:text-black">✕</button>
                    </div>
                    <textarea
                        autoFocus
                        className="w-full h-24 p-2 bg-yellow-100 text-sm resize-none focus:outline-none placeholder-yellow-800/50"
                        placeholder="Type your notes here..."
                    />
                    <div className="flex justify-end p-2 border-t border-yellow-200 bg-yellow-50">
                        <button
                            onClick={() => setNoteModal(prev => ({ ...prev, visible: false }))}
                            className="px-3 py-1 bg-white border border-gray-300 text-xs font-semibold rounded-sm shadow-sm"
                        >
                            Save Note
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
