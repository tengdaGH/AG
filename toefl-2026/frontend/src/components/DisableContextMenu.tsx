'use client';

import { useEffect } from 'react';
import { usePathname } from 'next/navigation';

export function DisableContextMenu() {
    const pathname = usePathname();

    useEffect(() => {
        // Ban right-click in test UIs and item preview/edit UIs
        const isTestUI = pathname?.startsWith('/test-session') || pathname?.startsWith('/ielts');
        const isItemUI = pathname?.includes('/items/'); // Any item UI (edit, preview, etc) or maybe just all of dashboard admin items? The user said "item UI", which usually means displaying an item.
        // Let's be broad based on the instruction "in all test UI and item UI".

        // Actually, let's explicitly block it on the specific routes:
        const shouldDisable = pathname?.startsWith('/test-session') ||
            pathname?.startsWith('/ielts') ||
            pathname?.includes('/items/') ||
            pathname?.includes('/demo/');

        if (shouldDisable) {
            const handleContextMenu = (e: MouseEvent) => {
                e.preventDefault();
            };

            document.addEventListener('contextmenu', handleContextMenu);

            return () => {
                document.removeEventListener('contextmenu', handleContextMenu);
            };
        }
    }, [pathname]);

    return null;
}
