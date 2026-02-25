'use client';

import React, { useState, useEffect } from 'react';

export interface StudentPost {
    id: string;
    authorName: string;
    avatarUrl?: string;
    text: string;
}

interface WriteAcademicDiscussionProps {
    instructionsHTML?: string;
    professorName?: string;
    professorAvatarUrl?: string;
    professorPromptHTML: string;
    studentPosts: StudentPost[];
    onSave?: (content: string) => void;
}

// Global declaration for the shared ETS clipboard
declare global {
    interface Window {
        ETS_Internal_Clipboard?: string;
    }
}

const Avatar = ({ src, name, size }: { src?: string; name: string; size: number }) => {
    const [error, setError] = useState(false);

    if (src && !error) {
        // eslint-disable-next-line @next/next/no-img-element
        return <img
            src={src}
            alt={name}
            style={{ width: `${size}px`, height: `${size}px`, borderRadius: '50%', objectFit: 'cover' }}
            onError={() => setError(true)}
        />;
    }

    return (
        <div style={{
            width: `${size}px`,
            height: `${size}px`,
            borderRadius: '50%',
            backgroundColor: '#eee',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
        }}>
            <span style={{ color: '#aaa', fontSize: size > 60 ? '16px' : '12px' }}>
                {name === "Professor" ? "Prof" : name[0]}
            </span>
        </div>
    );
};

export const WriteAcademicDiscussion: React.FC<WriteAcademicDiscussionProps> = ({
    instructionsHTML,
    professorName = "Professor",
    professorAvatarUrl = "/avatars/professor.png", // fallback placeholder path
    professorPromptHTML,
    studentPosts,
    onSave
}) => {
    const [content, setContent] = useState('');
    const [wordCount, setWordCount] = useState(0);
    const [showWordCount, setShowWordCount] = useState(true);

    const [history, setHistory] = useState<string[]>(['']);
    const [historyIndex, setHistoryIndex] = useState(0);

    const textareaRef = React.useRef<HTMLTextAreaElement>(null);

    const updateContent = (newContent: string) => {
        if (newContent !== content) {
            setContent(newContent);

            const newHistory = history.slice(0, historyIndex + 1);
            newHistory.push(newContent);
            if (newHistory.length > 100) newHistory.shift();

            setHistory(newHistory);
            setHistoryIndex(newHistory.length - 1);

            if (onSave) onSave(newContent);
        }
    };

    const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        updateContent(e.target.value);
    };

    useEffect(() => {
        const timer = setTimeout(() => {
            const words = content.trim().split(/\s+/).filter(Boolean).length;
            setWordCount(words);
        }, 200);
        return () => clearTimeout(timer);
    }, [content]);

    const blockNativeClipboard = (e: React.ClipboardEvent) => {
        e.preventDefault();
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
            {/* Left Pane: Instructions & Professor */}
            <div style={{
                flex: '0 0 38%',
                borderRight: '1px solid #767676',
                padding: '20px',
                fontSize: '16px',
                lineHeight: 1.4,
                display: 'flex',
                flexDirection: 'column'
            }}>
                <div style={{ marginBottom: '20px' }}>
                    {instructionsHTML ? (
                        <div dangerouslySetInnerHTML={{ __html: instructionsHTML }} />
                    ) : (
                        <div>
                            <p style={{ marginTop: 0 }}>Your professor is teaching a class on social studies. Write a post responding to the professor's question.</p>
                            <p style={{ fontWeight: 'bold' }}>In your response, you should do the following.</p>
                            <ul style={{ paddingLeft: '20px', margin: '10px 0' }}>
                                <li>Express and support your opinion.</li>
                                <li>Make a contribution to the discussion in your own words.</li>
                            </ul>
                            <p>An effective response will contain at least 100 words.</p>
                        </div>
                    )}
                </div>

                <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '15px' }}>
                    <Avatar src={professorAvatarUrl} name={professorName} size={100} />
                </div>

                <div style={{ flexGrow: 1 }} dangerouslySetInnerHTML={{ __html: professorPromptHTML }} />
            </div>

            {/* Right Pane: Student Posts & Response Sandbox */}
            <div style={{ flex: '1 1 62%', display: 'flex', flexDirection: 'column', padding: '20px' }}>

                {/* Student Posts List */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginBottom: '20px' }}>
                    {studentPosts.map((post) => (
                        <div key={post.id} style={{ display: 'flex', gap: '15px', alignItems: 'flex-start' }}>
                            <div style={{ flexShrink: 0 }}>
                                <Avatar src={post.avatarUrl} name={post.authorName} size={60} />
                            </div>
                            <div style={{ fontSize: '15px', lineHeight: 1.4 }}>
                                {post.text}
                            </div>
                        </div>
                    ))}
                </div>

                {/* Toolbar */}
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
