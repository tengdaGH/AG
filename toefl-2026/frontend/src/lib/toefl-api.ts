import { API_BASE_URL } from './api-config';

export interface TestItem {
    id: string;
    section: string;
    task_type: string;
    prompt_content: string;
    source_id: string;
}

export interface ParsedItem {
    id: string;
    section: string;
    task_type: string;
    source_id: string;
    content: any;
}

const headers = { 'Bypass-Tunnel-Reminder': 'true' };

/**
 * Fetches specific items for a set (e.g., ETS-S2)
 */
export async function fetchEtsSetItems(setId: string): Promise<ParsedItem[]> {
    try {
        // We'll use a search or filter endpoint if available, 
        // otherwise we might need to fetch all and filter client-side 
        // or add a new backend endpoint.
        // For now, let's assume we can filter by source_id prefix.
        const response = await fetch(`${API_BASE_URL}/api/items/filter?source_id_prefix=${setId}`, { headers });
        if (!response.ok) {
            throw new Error(`Failed to fetch items for set ${setId}`);
        }
        const items: TestItem[] = await response.json();

        return items.map(item => ({
            id: item.id,
            section: item.section,
            task_type: item.task_type,
            source_id: item.source_id,
            content: JSON.parse(item.prompt_content)
        }));
    } catch (error) {
        console.error('Error fetching ETS set items:', error);
        return [];
    }
}

/**
 * Alternative: Fetch items individually by source_id to ensure exact sequence
 */
export async function fetchSpecificEtsItems(sourceIds: string[]): Promise<ParsedItem[]> {
    const items: ParsedItem[] = [];
    for (const sid of sourceIds) {
        try {
            const res = await fetch(`${API_BASE_URL}/api/items/by-source/${sid}`, { headers });
            if (res.ok) {
                const item: TestItem = await res.json();
                items.push({
                    id: item.id,
                    section: item.section,
                    task_type: item.task_type,
                    source_id: item.source_id,
                    content: JSON.parse(item.prompt_content)
                });
            }
        } catch (e) {
            console.error(`Failed to fetch item ${sid}`, e);
        }
    }
    return items;
}
