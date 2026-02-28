"use client";

import React, { useState, useEffect } from "react";
import { Clock, Eye, EyeOff, Wifi, Bell, Menu } from "lucide-react";

interface IELTSHeaderProps {
    sectionName?: string;
    testTakerId?: string;
    onTimeExpired: () => void;
}

export default function IELTSHeader({
    sectionName = "Reading",
    testTakerId = "Test taker ID",
    onTimeExpired,
}: IELTSHeaderProps) {
    const [timeLeft, setTimeLeft] = useState(60 * 60); // 60 minutes
    const [showTime, setShowTime] = useState(true);

    useEffect(() => {
        if (timeLeft <= 0) {
            onTimeExpired();
            return;
        }
        const timer = setInterval(() => setTimeLeft((prev) => prev - 1), 1000);
        return () => clearInterval(timer);
    }, [timeLeft, onTimeExpired]);

    const minutes = Math.floor(timeLeft / 60);
    const seconds = timeLeft % 60;
    const formattedTime = `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;

    const isDanger = timeLeft <= 300;
    const isWarningPulse = (timeLeft <= 600 && timeLeft > 590) || (timeLeft <= 300 && timeLeft > 290);

    useEffect(() => {
        if (isWarningPulse) setShowTime(true);
    }, [isWarningPulse]);

    return (
        <header
            className="flex items-center px-4 flex-shrink-0 z-50 justify-between"
            style={{
                height: "48px",
                backgroundColor: "#F5F5F5",
                borderBottom: "1px solid #d9d9d9",
                fontFamily: "var(--ielts-font)",
                color: "#333333"
            }}
        >
            {/* Left: IELTS logo + section & Candidate ID */}
            <div className="flex items-center gap-6">
                <div className="flex items-center gap-3">
                    <span
                        style={{
                            color: "var(--ielts-logo-red)",
                            fontWeight: 800,
                            fontSize: "18px",
                            letterSpacing: "0.5px",
                        }}
                    >
                        IELTS
                    </span>
                    <span style={{ color: "#666", fontSize: "14px", fontWeight: 600 }}>
                        {sectionName}
                    </span>
                </div>

                {/* Generic Candidate ID profile block */}
                <div className="flex items-center gap-2 pl-5 border-l border-gray-300">
                    <span style={{ color: "#333", fontSize: "14px", fontWeight: 700 }}>
                        Candidate:
                    </span>
                    <span style={{ color: "#555", fontSize: "14px" }}>
                        {testTakerId}
                    </span>
                    <div className="flex items-center gap-2 ml-4">
                        <Wifi size={16} color="#999" />
                        <Bell size={16} color="#999" />
                        <Menu size={16} color="#999" />
                    </div>
                </div>
            </div>

            {/* Right: Timer strictly right-aligned with toggle */}
            <div className="flex items-center gap-4">
                <button
                    onClick={() => setShowTime(!showTime)}
                    className="flex items-center gap-1 text-gray-500 hover:text-gray-800 transition-colors"
                    style={{ fontSize: "13px", fontWeight: 600 }}
                >
                    {showTime ? <EyeOff size={16} /> : <Eye size={16} />}
                    <span>{showTime ? "Hide Time" : "Show Time"}</span>
                </button>

                <div
                    className="flex items-center gap-1.5 px-3 py-1 rounded transition-colors"
                    style={{
                        fontSize: "18px",
                        fontWeight: 700,
                        backgroundColor: isDanger ? "#c62828" : isWarningPulse ? "#c62828" : "transparent",
                        color: isDanger || isWarningPulse ? "#fff" : "#333",
                        animation: isWarningPulse ? "pulse 1s ease-in-out infinite" : undefined,
                        minWidth: "80px",
                        justifyContent: "flex-end"
                    }}
                >
                    <Clock size={16} style={{ color: isDanger || isWarningPulse ? "#fff" : "#333" }} />
                    {showTime ? (
                        <span suppressHydrationWarning>{formattedTime}</span>
                    ) : (
                        <span style={{ visibility: "hidden" }}>{formattedTime}</span>
                    )}
                </div>
            </div>
        </header>
    );
}
