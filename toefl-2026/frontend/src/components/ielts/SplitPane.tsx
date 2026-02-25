"use client";

import React, { useRef, useEffect, useState, useCallback } from "react";

interface SplitPaneProps {
    leftContent: React.ReactNode;
    rightContent: React.ReactNode;
    leftScrollTop?: number;
    rightScrollTop?: number;
    onLeftScroll?: (scrollTop: number) => void;
    onRightScroll?: (scrollTop: number) => void;
    colorScheme?: "standard" | "yellow-on-black" | "blue-on-white";
    textSize?: "standard" | "large" | "extra-large";
    rightPaneRef?: React.RefObject<HTMLDivElement | null>;
    leftPaneRef?: React.RefObject<HTMLDivElement | null>;
}

export default function SplitPane({
    leftContent,
    rightContent,
    leftScrollTop = 0,
    rightScrollTop = 0,
    onLeftScroll,
    onRightScroll,
    colorScheme = "standard",
    textSize = "standard",
    rightPaneRef,
    leftPaneRef,
}: SplitPaneProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const internalLeftRef = useRef<HTMLDivElement>(null);
    const internalRightRef = useRef<HTMLDivElement>(null);
    const activeLeftRef = leftPaneRef || internalLeftRef;
    const activeRightRef = rightPaneRef || internalRightRef;
    const [splitRatio, setSplitRatio] = useState(0.5);
    const [isDragging, setIsDragging] = useState(false);

    const handleLeftScroll = () => {
        if (activeLeftRef.current && onLeftScroll) onLeftScroll(activeLeftRef.current.scrollTop);
    };

    const handleRightScroll = () => {
        if (activeRightRef.current && onRightScroll) onRightScroll(activeRightRef.current.scrollTop);
    };

    const handleMouseDown = useCallback((e: React.MouseEvent) => {
        e.preventDefault();
        setIsDragging(true);
    }, []);

    const handleMouseMove = useCallback(
        (e: MouseEvent) => {
            if (!isDragging || !containerRef.current) return;
            const rect = containerRef.current.getBoundingClientRect();
            const ratio = (e.clientX - rect.left) / rect.width;
            setSplitRatio(Math.max(0.25, Math.min(0.75, ratio)));
        },
        [isDragging]
    );

    const handleMouseUp = useCallback(() => {
        setIsDragging(false);
    }, []);

    useEffect(() => {
        if (isDragging) {
            document.addEventListener("mousemove", handleMouseMove);
            document.addEventListener("mouseup", handleMouseUp);
            document.body.style.cursor = "col-resize";
            document.body.style.userSelect = "none";
        }
        return () => {
            document.removeEventListener("mousemove", handleMouseMove);
            document.removeEventListener("mouseup", handleMouseUp);
            document.body.style.cursor = "";
            document.body.style.userSelect = "";
        };
    }, [isDragging, handleMouseMove, handleMouseUp]);

    // Theme & sizing
    const themeClasses = {
        standard: "bg-white text-black",
        "yellow-on-black": "bg-black text-[#FFFF00]",
        "blue-on-white": "bg-white text-[#0000FF]",
    }[colorScheme];

    const sizeClasses = {
        standard: "text-base",
        large: "text-lg md:text-xl",
        "extra-large": "text-xl md:text-2xl",
    }[textSize];

    return (
        <div
            ref={containerRef}
            className={`flex flex-row w-full flex-1 overflow-hidden ${themeClasses} ${sizeClasses}`}
            style={{ fontFamily: "var(--ielts-font)" }}
        >
            {/* Left Pane: Passage */}
            <div
                ref={activeLeftRef}
                onScroll={handleLeftScroll}
                className="h-full overflow-y-auto relative"
                style={{
                    width: `${splitRatio * 100}%`,
                    padding: "40px 60px", // Increased padding for pleasant spacing
                }}
            >
                <div className="max-w-[900px] mx-auto h-full pb-32">
                    {leftContent}
                </div>
            </div>

            {/* Resizable Drag Handle */}
            <div
                onMouseDown={handleMouseDown}
                className="flex-shrink-0 flex items-center justify-center relative group"
                style={{
                    width: "8px",
                    backgroundColor: isDragging ? "#c0c0c0" : "#d9d9d9",
                    cursor: "col-resize",
                    transition: isDragging ? "none" : "background-color 0.15s",
                    zIndex: 20,
                }}
            >
                {/* Drag handle block — square with arrows */}
                <div
                    className="absolute flex items-center justify-center border shadow-sm"
                    style={{
                        width: "28px",
                        height: "28px",
                        left: "-10px",
                        cursor: "col-resize",
                        backgroundColor: "#F4F4F4", // Opaque background matching workspace to hide track
                        borderColor: "#999",
                        borderRadius: "2px",
                        color: "#666",
                    }}
                >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M8 8L4 12L8 16" />
                        <path d="M16 8L20 12L16 16" />
                        <line x1="4" y1="12" x2="20" y2="12" />
                    </svg>
                </div>
            </div>

            {/* Right Pane: Questions */}
            <div
                ref={activeRightRef}
                onScroll={handleRightScroll}
                className="h-full overflow-y-auto bg-white relative"
                style={{
                    width: `${(1 - splitRatio) * 100}%`,
                    padding: "40px 60px", // Increased padding for pleasant spacing
                }}
            >
                <div
                    className={`max-w-[900px] mx-auto h-full pb-32 ${colorScheme !== "standard" ? themeClasses : ""}`}
                >
                    {rightContent}
                </div>
            </div>
        </div>
    );
}
