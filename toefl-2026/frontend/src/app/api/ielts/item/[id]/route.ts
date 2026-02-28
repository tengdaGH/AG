import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET(
    request: NextRequest,
    context: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await context.params;

        let filename = id;
        if (!filename.endsWith('.json')) {
            filename += '.json';
        }

        // Use parsed_v2 directory (228+ items, full type codes)
        const parsedDir = path.resolve('/Users/tengda/Antigravity/IELTS/parsed_v2');
        const filePath = path.join(parsedDir, filename);

        if (!filePath.startsWith(parsedDir)) {
            return NextResponse.json({ error: 'Invalid file path' }, { status: 400 });
        }

        if (!fs.existsSync(filePath)) {
            return NextResponse.json({ error: 'Item not found' }, { status: 404 });
        }

        const fileContent = fs.readFileSync(filePath, 'utf-8');
        const raw = JSON.parse(fileContent);

        // Normalize parsed_v2 JSON shape into the format the workspace page expects
        const paragraphs = (raw.content?.paragraphs || []).map((p: any) => ({
            label: p.label || '',
            text: p.content || p.text || '',
        }));

        const questionGroups = (raw.questions?.question_groups || []).map((g: any) => {
            const questions = g.questions || [];
            const numbers = questions.map((q: any) => q.number).filter(Boolean);
            const rangeStart = numbers.length > 0 ? Math.min(...numbers) : 0;
            const rangeEnd = numbers.length > 0 ? Math.max(...numbers) : 0;

            return {
                type: g.type || 'UNKNOWN',
                range: [rangeStart, rangeEnd],
                instructions: g.instruction || g.instructions || '',
                questions: questions.map((q: any) => ({
                    number: q.number,
                    text: q.question_text || '',
                    options: q.options || null,
                    answer: q.answer || null,
                })),
            };
        });

        // Compute overall question range
        const allNumbers = questionGroups.flatMap((g: any) =>
            g.questions.map((q: any) => q.number)
        ).filter(Boolean);
        const questionRange = allNumbers.length > 0
            ? [Math.min(...allNumbers), Math.max(...allNumbers)]
            : [1, 13];

        const normalized = {
            id: raw.id,
            title: raw.title || raw.content?.title || 'Untitled',
            question_range: questionRange,
            passage: {
                has_paragraph_labels: raw.content?.has_paragraph_labels ?? false,
                paragraphs,
            },
            question_groups: questionGroups,
        };

        return NextResponse.json(normalized);
    } catch (error) {
        console.error('Error fetching IELTS item:', error);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}
