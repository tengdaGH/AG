'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { testLogger } from '../lib/testLogger';

interface WriteEmailProps {
    promptHTML: string;
    emailTo?: string;
    emailSubject?: string;
    onSave?: (content: string) => void;
}

// Ensure the isolated ETS clipboard exists globally without bleeding out
declare global {
    interface Window {
        ETS_Internal_Clipboard?: string;
    }
}

export const WriteEmail: React.FC<WriteEmailProps> = ({ promptHTML, emailTo = "editor@sunshinepoetrymagazine.com", emailSubject = "Problem using submission form", onSave }) => {
    const [content, setContent] = useState('');
    const [wordCount, setWordCount] = useState(0);
    const [showWordCount, setShowWordCount] = useState(true);

    // History for Undo/Redo
    const [history, setHistory] = useState<string[]>(['']);
    const [historyIndex, setHistoryIndex] = useState(0);

    const textareaRef = React.useRef<HTMLTextAreaElement>(null);

    const updateContent = (newContent: string) => {
        if (newContent !== content) {
            setContent(newContent);

            // Only add to history if it's a new state to avoid duplicates
            const newHistory = history.slice(0, historyIndex + 1);
            newHistory.push(newContent);
            if (newHistory.length > 100) newHistory.shift(); // Limit history depth

            setHistory(newHistory);
            setHistoryIndex(newHistory.length - 1);

            if (onSave) onSave(newContent);
        }
    };

    const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        const val = e.target.value;
        const diffLength = val.length - content.length;

        // Log keystroke metrics
        testLogger.logEvent('KEYSTROKE', 'WRITE_EMAIL_TASK', {
            diffLength,
            wordCount,
            timestamp_ms: Date.now()
        });

        updateContent(val);
    };

    // CJK-aware word count
    useEffect(() => {
        const timer = setTimeout(() => {
            const trimmed = content.trim();
            if (!trimmed) { setWordCount(0); return; }
            const cjkChars = trimmed.match(/[\u4e00-\u9fff\u3400-\u4dbf\uac00-\ud7af\u3040-\u309f\u30a0-\u30ff]/g);
            if (cjkChars && cjkChars.length > trimmed.split(/\s+/).filter(Boolean).length) {
                setWordCount(Math.ceil(cjkChars.length / 1.5));
            } else {
                setWordCount(trimmed.split(/\s+/).filter(Boolean).length);
            }
        }, 200);
        return () => clearTimeout(timer);
    }, [content]);

    // OS Clipboard Intercepts
    const blockNativeClipboard = (e: React.ClipboardEvent) => {
        e.preventDefault();
        testLogger.logEvent('NATIVE_CLIPBOARD_BLOCKED', 'WRITE_EMAIL_TASK', { type: e.type });
    };

    const handleCustomCut = () => {
        if (!textareaRef.current) return;
        const start = textareaRef.current.selectionStart;
        const end = textareaRef.current.selectionEnd;
        if (start !== end) {
            const selectedText = content.substring(start, end);
            window.ETS_Internal_Clipboard = selectedText;
            const newContent = content.substring(0, start) + content.substring(end);
            updateContent(newContent);

            setTimeout(() => {
                if (textareaRef.current) {
                    textareaRef.current.selectionStart = textareaRef.current.selectionEnd = start;
                    textareaRef.current.focus();
                }
            }, 0);
        }
    };

    const handleCustomPaste = () => {
        if (!textareaRef.current || !window.ETS_Internal_Clipboard) return;
        const start = textareaRef.current.selectionStart;
        const end = textareaRef.current.selectionEnd;
        const pasteText = window.ETS_Internal_Clipboard;
        const newContent = content.substring(0, start) + pasteText + content.substring(end);

        testLogger.logEvent('CUSTOM_CLIPBOARD_PASTE', 'WRITE_EMAIL_TASK', { pasted_length: pasteText.length });

        updateContent(newContent);

        const newCursorPos = start + pasteText.length;
        setTimeout(() => {
            if (textareaRef.current) {
                textareaRef.current.selectionStart = textareaRef.current.selectionEnd = newCursorPos;
                textareaRef.current.focus();
            }
        }, 0);
    };

    const handleUndo = () => {
        if (historyIndex > 0) {
            const newIndex = historyIndex - 1;
            setHistoryIndex(newIndex);
            setContent(history[newIndex]);
            if (onSave) onSave(history[newIndex]);
            textareaRef.current?.focus();
        }
    };

    const handleRedo = () => {
        if (historyIndex < history.length - 1) {
            const newIndex = historyIndex + 1;
            setHistoryIndex(newIndex);
            setContent(history[newIndex]);
            if (onSave) onSave(history[newIndex]);
            textareaRef.current?.focus();
        }
    };

    const toolbarButtonStyle: React.CSSProperties = {
        padding: '2px 8px',
        marginRight: '2px',
        backgroundColor: '#f0f0f0',
        border: '1px solid #888',
        borderRadius: '3px',
        fontSize: '12px',
        fontFamily: 'Arial, sans-serif',
        cursor: 'pointer',
        color: '#000',
        fontWeight: 'normal'
    };

    return (
        <div style={{
            display: 'flex',
            width: '100%',
            height: '100%',
            backgroundColor: '#FFFFFF',
            border: '1px solid #767676',
            fontFamily: '"Times New Roman", Times, serif',
            color: '#000'
        }}>
            {/* Left Pane: Prompt */}
            <div
                style={{
                    flex: '0 0 38%',
                    borderRight: '1px solid #767676',
                    padding: '20px',
                    fontSize: '16px',
                    lineHeight: 1.4,
                }}
            >
                <div dangerouslySetInnerHTML={{ __html: promptHTML }} />
            </div>

            {/* Right Pane: Live Editor Sandbox */}
            <div style={{ flex: '1 1 62%', display: 'flex', flexDirection: 'column', padding: '20px' }}>

                {/* Header Information */}
                <div style={{ marginBottom: '15px' }}>
                    <div style={{ fontWeight: 'bold', fontSize: '16px', marginBottom: '15px' }}>
                        Your Response:
                    </div>
                    <div style={{ fontSize: '15px', fontFamily: '"Times New Roman", Times, serif', marginBottom: '2px' }}>
                        <span style={{ fontWeight: 'bold' }}>To: </span>{emailTo}
                    </div>
                    <div style={{ fontSize: '15px', fontFamily: '"Times New Roman", Times, serif' }}>
                        <span style={{ fontWeight: 'bold' }}>Subject: </span>{emailSubject}
                    </div>
                </div>

                {/* ETS Toolbar (Sandbox rules) */}
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    marginBottom: '5px'
                }}>
                    <button onClick={handleCustomCut} style={toolbarButtonStyle}>Cut</button>
                    <button onClick={handleCustomPaste} style={{ ...toolbarButtonStyle, color: typeof window !== 'undefined' && window.ETS_Internal_Clipboard ? '#000' : '#888' }}>Paste</button>
                    <button onClick={handleUndo} disabled={historyIndex === 0} style={{ ...toolbarButtonStyle, color: historyIndex === 0 ? '#888' : '#000', cursor: historyIndex === 0 ? 'default' : 'pointer' }}>Undo</button>
                    <button onClick={handleRedo} disabled={historyIndex === history.length - 1} style={{ ...toolbarButtonStyle, color: historyIndex === history.length - 1 ? '#888' : '#000', cursor: historyIndex === history.length - 1 ? 'default' : 'pointer' }}>Redo</button>

                    <button
                        onClick={() => setShowWordCount(!showWordCount)}
                        style={{ ...toolbarButtonStyle, marginLeft: '50px', fontWeight: 'bold', border: '2px solid #333', color: '#000', padding: '1px 8px' }}
                    >
                        {showWordCount ? 'Hide Word Count' : 'Show Word Count'}
                    </button>

                    <div style={{ marginLeft: '80px', fontSize: '15px', fontFamily: 'Arial, sans-serif', color: '#000' }}>
                        {showWordCount ? wordCount : ''}
                    </div>
                </div>

                {/* Secure Textarea */}
                <textarea
                    ref={textareaRef}
                    value={content}
                    onChange={handleInput}
                    onCopy={blockNativeClipboard}
                    onCut={blockNativeClipboard}
                    onPaste={blockNativeClipboard}
                    style={{
                        flexGrow: 1,
                        fontSize: '16px',
                        lineHeight: 1.5,
                        color: '#000',
                        border: '1px solid #a0a0a0',
                        resize: 'none',
                        outline: 'none',
                        fontFamily: 'Arial, Helvetica, sans-serif',
                        padding: '10px'
                    }}
                />
            </div>
        </div>
    );
};
