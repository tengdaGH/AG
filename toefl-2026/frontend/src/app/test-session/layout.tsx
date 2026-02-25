import React from 'react';
import type { Metadata } from 'next';

export const metadata: Metadata = {
    title: 'Secure Testing Session | TOEFL 2026',
    description: 'Proctored examination environment',
};

// This layout strips away typical global styles for the test session 
// and enforces the ETS 100vw x 100vh lock inside its subcomponents.
export default function TestSessionLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <React.Fragment>
            {children}
        </React.Fragment>
    );
}
