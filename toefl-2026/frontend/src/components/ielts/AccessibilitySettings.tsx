import React from "react";
import { X } from "lucide-react";

export type ColorScheme = "standard" | "yellow-on-black" | "blue-on-white";
export type TextSize = "standard" | "large" | "extra-large";

interface AccessibilitySettingsProps {
    isOpen: boolean;
    onClose: () => void;
    colorScheme: ColorScheme;
    setColorScheme: (scheme: ColorScheme) => void;
    textSize: TextSize;
    setTextSize: (size: TextSize) => void;
}

export default function AccessibilitySettings({
    isOpen,
    onClose,
    colorScheme,
    setColorScheme,
    textSize,
    setTextSize,
}: AccessibilitySettingsProps) {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/50 z-[100] flex items-center justify-center backdrop-blur-sm">
            <div className="bg-white rounded-lg shadow-xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                <div className="flex items-center justify-between p-4 border-b">
                    <h2 className="text-xl font-bold text-gray-800">Accessibility Settings</h2>
                    <button onClick={onClose} className="text-gray-500 hover:text-gray-800 transition-colors">
                        <X size={24} />
                    </button>
                </div>

                <div className="p-6 space-y-6">
                    {/* Text Size */}
                    <div className="space-y-3">
                        <h3 className="font-semibold text-gray-700">Text Size</h3>
                        <div className="flex flex-col gap-2">
                            {(["standard", "large", "extra-large"] as TextSize[]).map((size) => (
                                <label key={size} className="flex items-center gap-3 cursor-pointer p-2 hover:bg-gray-50 rounded-md">
                                    <input
                                        type="radio"
                                        name="textSize"
                                        value={size}
                                        checked={textSize === size}
                                        onChange={() => setTextSize(size)}
                                        className="w-4 h-4 accent-[#002D62]"
                                    />
                                    <span className="capitalize">{size.replace("-", " ")}</span>
                                </label>
                            ))}
                        </div>
                    </div>

                    {/* Color Scheme */}
                    <div className="space-y-3">
                        <h3 className="font-semibold text-gray-700">Color Scheme</h3>
                        <div className="flex flex-col gap-2">
                            <label className="flex items-center gap-3 cursor-pointer p-2 hover:bg-gray-50 rounded-md">
                                <input
                                    type="radio"
                                    name="colorScheme"
                                    checked={colorScheme === "standard"}
                                    onChange={() => setColorScheme("standard")}
                                    className="w-4 h-4 accent-[#002D62]"
                                />
                                <div className="flex items-center gap-2">
                                    <span>Standard</span>
                                    <div className="w-6 h-6 border border-gray-300 bg-white shadow-sm rounded-sm"></div>
                                </div>
                            </label>

                            <label className="flex items-center gap-3 cursor-pointer p-2 hover:bg-gray-50 rounded-md">
                                <input
                                    type="radio"
                                    name="colorScheme"
                                    checked={colorScheme === "yellow-on-black"}
                                    onChange={() => setColorScheme("yellow-on-black")}
                                    className="w-4 h-4 accent-[#002D62]"
                                />
                                <div className="flex items-center gap-2">
                                    <span>Yellow on Black</span>
                                    <div className="w-6 h-6 border border-gray-600 bg-black flex items-center justify-center rounded-sm">
                                        <div className="w-3 h-3 bg-[#FFFF00] rounded-sm"></div>
                                    </div>
                                </div>
                            </label>

                            <label className="flex items-center gap-3 cursor-pointer p-2 hover:bg-gray-50 rounded-md">
                                <input
                                    type="radio"
                                    name="colorScheme"
                                    checked={colorScheme === "blue-on-white"}
                                    onChange={() => setColorScheme("blue-on-white")}
                                    className="w-4 h-4 accent-[#002D62]"
                                />
                                <div className="flex items-center gap-2">
                                    <span>Blue on White</span>
                                    <div className="w-6 h-6 border border-blue-200 bg-white flex items-center justify-center shadow-sm rounded-sm">
                                        <div className="w-3 h-3 bg-[#0000FF] rounded-sm"></div>
                                    </div>
                                </div>
                            </label>
                        </div>
                    </div>
                </div>

                <div className="p-4 border-t bg-gray-50 flex justify-end">
                    <button
                        onClick={onClose}
                        className="px-6 py-2 bg-[#002D62] text-white font-medium rounded-md hover:bg-blue-900 transition-colors"
                    >
                        Done
                    </button>
                </div>
            </div>
        </div>
    );
}
