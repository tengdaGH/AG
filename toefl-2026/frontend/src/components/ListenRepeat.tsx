import React, { useState, useEffect } from 'react';
import { useLanguage } from '@/lib/i18n/LanguageContext';

export interface ListenRepeatProps {
    imageUrl: string;
    imageAlt?: string;
    audioUrl?: string;     // URL for the stimulus audio
    onAudioEnd?: () => void;
}

export function ListenRepeat({ imageUrl, imageAlt = "Listen and repeat context", audioUrl, onAudioEnd }: ListenRepeatProps) {
    const { t } = useLanguage();
    const [isPlaying, setIsPlaying] = useState(false);

    // Use a direct fallback check incase the translation function returns the raw key
    const translation = t('test.listenAndRepeatOnlyOnce');
    const instructionText = translation === 'test.listenAndRepeatOnlyOnce' ? 'Listen and repeat only once.' : translation;

    // In a real integration, we would play the audioUrl here on mount or via a sequencer.
    // For the UI rendering match, the focus is the visual layout.
    useEffect(() => {
        if (audioUrl) {
            // Placeholder: Logic to play audio would go here.
            // Example:
            // const audio = new Audio(audioUrl);
            // audio.play();
            // audio.onended = () => { setIsPlaying(false); onAudioEnd?.(); }
        }
    }, [audioUrl, onAudioEnd]);

    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'flex-start',
            width: '100%',
            height: '100%',
            backgroundColor: '#FFFFFF',
            border: '1px solid #767676',
            boxSizing: 'border-box',
            padding: '80px 20px', // More vertical space to match Figure 11
            fontFamily: 'Arial, sans-serif' // Standard ETS sans-serif for instructions
        }}>

            {/* Instructional Header */}
            <h2 style={{
                color: '#137882', // Darker ETS Teal matching Figure 11 closely
                fontSize: '28px',
                fontWeight: 'bold',
                fontFamily: '"Times New Roman", Times, serif', // Figure 11 uses a serif font for this specific instruction
                margin: '0 0 60px 0',
                textAlign: 'center'
            }}>
                {instructionText}
            </h2>

            {/* Contextual Image Container */}
            <div style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                maxWidth: '600px', // Restrict image width to maintain ratio and match mockup
                width: '100%'
            }}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                    src={imageUrl}
                    alt={imageAlt}
                    style={{
                        width: '100%',
                        height: 'auto',
                        border: '1px solid #767676', // Match the outer container border color exactly for a flat, formal look
                        display: 'block'
                    }}
                />
            </div>

            {/* 
              Note: The "Recording" state is often handled by a global or shared component 
              (like a sticky bottom bar or overlay) in actual operation. 
              The core Figure 11 UI is just the instruction and image.
            */}

        </div>
    );
}
