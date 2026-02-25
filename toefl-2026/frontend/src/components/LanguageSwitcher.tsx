'use client';

import React from 'react';
import { useLanguage } from '@/lib/i18n/LanguageContext';

export function LanguageSwitcher() {
    const { language, setLanguage } = useLanguage();

    const toggleLanguage = () => {
        setLanguage(language === 'en' ? 'zh' : 'en');
    };

    return (
        <button
            onClick={toggleLanguage}
            style={{
                padding: '6px 12px',
                backgroundColor: 'var(--card-bg)',
                border: '1px solid var(--border-color)',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '0.875rem',
                fontWeight: 500,
                color: 'var(--foreground)',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                transition: 'all 0.2s ease',
            }}
            title="Toggle English / Chinese"
        >
            <span role="img" aria-label="Globe">🌐</span>
            <span>{language === 'en' ? 'EN / 中文' : '中文 / EN'}</span>
        </button>
    );
}
