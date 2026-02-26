export interface Question {
    question_num: number;
    text: string;
    options: string[];
    correct_answer: number;
    audioUrl?: string;
    timeLimit?: number;
}

export interface ParsedContent {
    type: string;
    title: string;
    text: string;
    questions: Question[];
    hints?: string[];
    audioUrl?: string;
    script?: string;
}

export const TASK_TYPE_LABELS: Record<string, string> = {
    'READ_ACADEMIC_PASSAGE': 'Read an Academic Passage',
    'READ_IN_DAILY_LIFE': 'Read in Daily Life',
    'COMPLETE_THE_WORDS': 'Complete the Words',
    'BUILD_A_SENTENCE': 'Build a Sentence',
    'WRITE_ACADEMIC_DISCUSSION': 'Write for Academic Discussion',
    'WRITE_AN_EMAIL': 'Write an Email',
    'TAKE_AN_INTERVIEW': 'Take an Interview',
    'LISTEN_AND_REPEAT': 'Listen and Repeat',
    'LISTEN_CHOOSE_RESPONSE': 'Listen and Choose a Response',
    'LISTEN_ACADEMIC_TALK': 'Listen to an Academic Talk',
    'LISTEN_ANNOUNCEMENT': 'Listen to an Announcement',
    'LISTEN_CONVERSATION': 'Listen to a Conversation',
};

export function normaliseContent(raw: any, item: any): ParsedContent {
    // Resolve type: prefer human-readable task_type, then raw.type, then section
    const type = TASK_TYPE_LABELS[item.task_type]
        || raw.type
        || item.task_type
        || item.section || 'Unknown';

    // Resolve title: prioritize formal fields, fallback to generating from content
    let title = raw.title || raw.topic || raw.subject || raw.shortDescEn || raw.shortDesc || raw.id;

    // For WAD items, the topic is usually the title.
    if (!title && item.task_type === 'WRITE_ACADEMIC_DISCUSSION' && raw.topic) {
        title = raw.topic;
    }

    let rawTextForSnippet = raw.text || raw.content || raw.situation || raw.scenario || raw.professor_prompt || raw.professorQuestion || raw.question || '';
    if (typeof rawTextForSnippet === 'object' && rawTextForSnippet !== null) {
        rawTextForSnippet = rawTextForSnippet.text || rawTextForSnippet.content || '';
    }
    const textSnippet = typeof rawTextForSnippet === 'string' ? rawTextForSnippet.slice(0, 50).trim() : '';

    if (!title || title === raw.id) {
        if (textSnippet) {
            const cleanSnippet = textSnippet.replace(/\n/g, ' ').replace(/\s+/g, ' ');
            title = (title && title !== raw.id ? `${title}: ` : '') + (cleanSnippet.length >= 50 ? cleanSnippet + '...' : cleanSnippet);
        } else {
            title = 'Untitled Item';
        }
    }

    // Resolve passage text: handle diverse schemas (Professor Question, Students, Scenario, Bullets)
    let text = raw.text || raw.passage || raw.content || raw.situation || raw.scenario || raw.professor_prompt || raw.professorQuestion || raw.question || '';
    if (typeof text === 'object' && text !== null) {
        text = text.text || text.content || '';
    }

    // Append students for Academic Discussion
    if (raw.studentA || raw.studentB || raw.posts || raw.student_1_response) {
        const posts = [];
        if (raw.studentA) posts.push(`**${raw.studentA.name || 'Student A'}:** ${raw.studentA.text || raw.studentA.opinion || raw.studentA['观点'] || ''}`);
        if (raw.studentB) posts.push(`**${raw.studentB.name || 'Student B'}:** ${raw.studentB.text || raw.studentB.opinion || raw.studentB['观点'] || ''}`);

        // New WAD schema support
        if (raw.student_1_response) posts.push(`**${raw.student_1_name || 'Student 1'}:** ${raw.student_1_response}`);
        if (raw.student_2_response) posts.push(`**${raw.student_2_name || 'Student 2'}:** ${raw.student_2_response}`);

        if (Array.isArray(raw.posts)) {
            raw.posts.forEach((p: any) => {
                posts.push(`**${p.author || p.name || 'Student'}:** ${p.text || p.opinion || p['观点'] || ''}`);
            });
        }

        text += (text ? '\n\n' : '') + posts.join('\n\n');
    }

    // Append bullets for Email
    if (Array.isArray(raw.bullets) && raw.bullets.length > 0) {
        text += '\n\n**Task Requirements:**\n' + raw.bullets.map((b: string) => `• ${b}`).join('\n');
    }

    // Append sentences for Listen and Repeat
    if (Array.isArray(raw.sentences) && raw.sentences.length > 0) {
        text += (text ? '\n\n' : '') + '**Sentences:**\n' + raw.sentences.map((s: any) => `• ${s.text}`).join('\n');
    }

    // Normalise questions array
    const rawQuestions = raw.questions || [];
    const questions: Question[] = rawQuestions.map((q: any, i: number) => {
        // Handle case where question text is an object
        let questionText = typeof q.text === 'object' && q.text !== null ? q.text.text : (q.text || q.question || '');

        // Strip leading question number (e.g. "13. What is..." → "What is...")
        // so numbering is always sequential per item, not from the source PDF
        questionText = String(questionText).replace(/^\s*\d+\.\s*/, '');

        // Handle case where options are objects
        const options = (q.options || []).map((opt: any) =>
            typeof opt === 'object' && opt !== null ? opt.text : opt
        );

        return {
            question_num: i + 1,
            text: questionText,
            options: options,
            correct_answer: q.correct_answer ?? q.correct ?? 0,
            audioUrl: q.audioUrl || q.audio_url || q.audio_file,
            timeLimit: q.timeLimit,
        };
    });

    const hints = raw.hints || [];
    const audioUrl = raw.audio_url || raw.audioUrl || raw.audio_file || raw.audio || raw.audio_path || item.media_url;
    const script = raw.script || raw.transcript || raw.listening_script || raw.audio_script;

    return { type, title, text, questions, hints, audioUrl, script };
}

export function getItemAge(createdAt: string | null): string {
    if (!createdAt) return '—';
    const created = new Date(createdAt);
    const now = new Date();
    const diffMs = now.getTime() - created.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return '1 day';
    if (diffDays < 30) return `${diffDays} days`;
    if (diffDays < 365) return `${Math.floor(diffDays / 30)} mo`;
    return `${Math.floor(diffDays / 365)}y ${Math.floor((diffDays % 365) / 30)}mo`;
}
