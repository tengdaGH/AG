import React from 'react';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
    return (
        <div style={{ minHeight: '100vh', background: '#f8fafc', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
            <header style={{ background: '#1e293b', color: 'white', padding: '16px 32px', display: 'flex', alignItems: 'center', boxShadow: '0 4px 10px rgba(0,0,0,0.1)', position: 'sticky', top: 0, zIndex: 100 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div style={{ background: '#006A70', color: 'white', padding: '8px 12px', borderRadius: 8, fontWeight: 800, letterSpacing: 1 }}>ETS</div>
                    <span style={{ fontSize: 20, fontWeight: 600, letterSpacing: 0.5 }}>Rater Portal</span>
                </div>
            </header>
            <main style={{ padding: '32px', maxWidth: '1280px', margin: '0 auto' }}>
                {children}
            </main>
        </div>
    );
}
