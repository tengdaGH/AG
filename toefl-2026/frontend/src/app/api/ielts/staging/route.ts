import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

const STAGING_DIR = '/Users/tengda/Antigravity/IELTS/staging';

export async function GET() {
    try {
        const files = fs.readdirSync(STAGING_DIR)
            .filter(f => f.endsWith('.json'))
            .sort();

        const items = files.map(filename => {
            const id = filename.replace('.json', '');
            try {
                const raw = JSON.parse(fs.readFileSync(path.join(STAGING_DIR, filename), 'utf-8'));
                const title = raw.title || raw.content?.title || id;
                const questionCount = raw.questions?.parsed_total_questions ?? 0;
                const qTypes = (raw.questions?.question_groups || [])
                    .map((g: any) => g.type)
                    .filter(Boolean);
                return { id, title, questionCount, questionTypes: [...new Set(qTypes)] };
            } catch {
                return { id, title: id, questionCount: 0, questionTypes: [] };
            }
        });

        return NextResponse.json({ items, total: items.length });
    } catch (error) {
        console.error('Error listing staging items:', error);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}
