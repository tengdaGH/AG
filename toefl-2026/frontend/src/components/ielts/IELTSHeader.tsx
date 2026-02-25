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
            className="flex items-center justify-between px-4 flex-shrink-0 z-50"
            style={{
                height: "48px",
                backgroundColor: "var(--ielts-header-bg)",
                fontFamily: "var(--ielts-font)",
            }}
        >
            {/* Left: IELTS logo + section */}
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
                <span style={{ color: "#aaa", fontSize: "13px" }}>
                    {sectionName}
                </span>
            </div>

            {/* Center: Timer */}
            <div className="flex items-center gap-2">
                <button
                    onClick={() => setShowTime(!showTime)}
                    className="flex items-center gap-1 text-gray-400 hover:text-white transition-colors"
                    style={{ fontSize: "12px" }}
                >
                    {showTime ? <EyeOff size={14} /> : <Eye size={14} />}
                    <span>{showTime ? "Hide" : "Show"}</span>
                </button>

                <div
                    className="flex items-center gap-1.5 px-3 py-1 rounded font-mono transition-colors"
                    style={{
                        fontSize: "15px",
                        fontWeight: 700,
                        backgroundColor: isDanger ? "#c62828" : isWarningPulse ? "#c62828" : "rgba(255,255,255,0.1)",
                        color: isDanger || isWarningPulse ? "#fff" : "#ccc",
                        animation: isWarningPulse ? "pulse 1s ease-in-out infinite" : undefined,
                    }}
                >
                    <Clock size={14} />
                    {showTime ? (
                        <span suppressHydrationWarning>{formattedTime}</span>
                    ) : (
                        <span style={{ visibility: "hidden" }}>{formattedTime}</span>
                    )}
                </div>
            </div>

            {/* Right: Test taker + icons */}
            <div className="flex items-center gap-4">
                <span style={{ color: "#999", fontSize: "13px" }}>
                    {testTakerId}
                </span>
                <div className="flex items-center gap-2">
                    <Wifi size={16} color="#999" />
                    <Bell size={16} color="#999" />
                    <Menu size={16} color="#999" />
                </div>
            </div>
        </header>
    );
}
