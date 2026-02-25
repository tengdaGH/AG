# ============================================================
# Purpose:       Generate ~32 Take an Interview speaking items with 4-stage prompts (A2–C1) to reach 10-form capacity.
# Usage:         python agents/scripts/populate_interviews.py
# Created:       2026-02-25
# Self-Destruct: No
# ============================================================
"""
Generate ~32 Take an Interview items to reach the 10-form target of 40.
Each interview has 4 progressive prompts: Personal Experience → Personal Reaction → Opinion → Recommendation.
"""
import os, sys, json, uuid, re, time, signal
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Force unbuffered stdout
os.environ['PYTHONUNBUFFERED'] = '1'

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend'))
sys.path.append(backend_dir)

from app.database.connection import SessionLocal, engine, Base
from app.models.models import TestItem, SectionType, CEFRLevel, TaskType, ItemStatus

Base.metadata.create_all(bind=engine)
load_dotenv(os.path.join(backend_dir, '.env'))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Please set GEMINI_API_KEY in backend/.env.")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

manual_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../rr_25_12_extracted.txt'))
with open(manual_path, 'r', encoding='utf-8', errors='ignore') as f:
    manual_text = f.read()[:10000]

# ─── 32 Interview Scenarios ─────────────────────────────────────────────────
SCENARIOS = [
    # A2 level (8 scenarios) — simpler, concrete topics
    {"topic": "Neighborhood Life", "scenario": "A research study about people's experiences living in their neighborhoods.", "level": "A2", "diff": -1.0},
    {"topic": "School Meals", "scenario": "A research study about students' eating habits and preferences for school meals.", "level": "A2", "diff": -0.8},
    {"topic": "Public Transportation", "scenario": "A research study about how people use public transportation in their daily lives.", "level": "A2", "diff": -0.6},
    {"topic": "Weekend Activities", "scenario": "A research study about how people spend their free time on weekends.", "level": "A2", "diff": -1.0},
    {"topic": "Shopping Habits", "scenario": "A research study about people's shopping preferences and habits.", "level": "A2", "diff": -0.8},
    {"topic": "Pets and Animals", "scenario": "A research study about people's experiences with pets and their attitudes toward animals.", "level": "A2", "diff": -0.6},
    {"topic": "Cooking at Home", "scenario": "A research study about people's experiences cooking at home versus eating out.", "level": "A2", "diff": -0.8},
    {"topic": "Learning a New Skill", "scenario": "A research study about people's experiences learning something new.", "level": "A2", "diff": -0.6},

    # B1 level (8 scenarios) — moderate complexity
    {"topic": "Volunteering", "scenario": "A research study about volunteering experiences and community service.", "level": "B1", "diff": 0.0},
    {"topic": "Study Abroad", "scenario": "A research study about students' experiences studying in a foreign country.", "level": "B1", "diff": 0.2},
    {"topic": "Campus Housing", "scenario": "A research study about university housing options and student living preferences.", "level": "B1", "diff": 0.0},
    {"topic": "Social Media and Communication", "scenario": "A research study about how social media has changed the way people communicate.", "level": "B1", "diff": 0.2},
    {"topic": "Part-Time Jobs", "scenario": "A research study about students' experiences with part-time employment during their studies.", "level": "B1", "diff": 0.0},
    {"topic": "Sports and Fitness", "scenario": "A research study about people's attitudes toward sports and physical fitness.", "level": "B1", "diff": 0.2},
    {"topic": "Music and Culture", "scenario": "A research study about how music influences people's moods and cultural identity.", "level": "B1", "diff": 0.0},
    {"topic": "Environmental Awareness", "scenario": "A research study about how young people are responding to environmental challenges.", "level": "B1", "diff": 0.2},

    # B2 level (8 scenarios) — more analytically demanding
    {"topic": "Digital Learning", "scenario": "A research study about the effectiveness of online education compared to traditional classroom learning.", "level": "B2", "diff": 0.8},
    {"topic": "Career Planning", "scenario": "A research study about how university students plan their careers and make professional decisions.", "level": "B2", "diff": 1.0},
    {"topic": "Cultural Diversity on Campus", "scenario": "A research study about how cultural diversity on university campuses affects students' learning experiences.", "level": "B2", "diff": 0.8},
    {"topic": "Mental Health and Wellbeing", "scenario": "A research study about mental health awareness and support services for university students.", "level": "B2", "diff": 1.0},
    {"topic": "Sustainable Living", "scenario": "A research study about sustainable lifestyle choices and their impact on the environment.", "level": "B2", "diff": 0.8},
    {"topic": "Leadership Experiences", "scenario": "A research study about leadership experiences and skills development among university students.", "level": "B2", "diff": 1.0},
    {"topic": "Technology and Privacy", "scenario": "A research study about how technology affects personal privacy in modern life.", "level": "B2", "diff": 0.8},
    {"topic": "Scholarship Application", "scenario": "You are applying for a merit-based scholarship. The scholarship committee will interview you about your qualifications.", "level": "B2", "diff": 1.0},

    # C1 level (8 scenarios) — complex, abstract, argumentative
    {"topic": "Artificial Intelligence in Education", "scenario": "A research study about the role of artificial intelligence in shaping the future of education.", "level": "C1", "diff": 1.5},
    {"topic": "Globalization and Local Identity", "scenario": "A research study about how globalization affects local cultural identities and traditions.", "level": "C1", "diff": 1.8},
    {"topic": "Research Ethics", "scenario": "A research study about ethical considerations in academic research and scientific experimentation.", "level": "C1", "diff": 1.5},
    {"topic": "Urban Planning and Quality of Life", "scenario": "A research study about how urban planning decisions affect residents' quality of life.", "level": "C1", "diff": 1.8},
    {"topic": "Media Literacy", "scenario": "A research study about the importance of media literacy in the age of misinformation.", "level": "C1", "diff": 1.5},
    {"topic": "Academic Collaboration", "scenario": "A research study about the benefits and challenges of collaborative academic work.", "level": "C1", "diff": 1.8},
    {"topic": "Innovation and Entrepreneurship", "scenario": "A research study about how universities can foster innovation and entrepreneurial thinking.", "level": "C1", "diff": 1.5},
    {"topic": "Work-Life Integration", "scenario": "A research study about changing attitudes toward work-life balance in the modern workplace.", "level": "C1", "diff": 1.8},
]


def build_prompt(scenario):
    return f"""Generate ONE TOEFL 2026 "Take an Interview" item as a JSON object.

SCENARIO: "{scenario['topic']}" — {scenario['scenario']}
CEFR Level: {scenario['level']}

The interview has EXACTLY 4 questions that progress in complexity:
1. "Personal Experience" — asks about a concrete personal experience related to the topic (factual, straightforward)
2. "Personal Reaction" — asks about the test taker's emotional/psychological reaction to the topic (more reflective)
3. "Opinion" — presents a claim and asks whether the test taker agrees or disagrees, with reasoning
4. "Prediction/Recommendation" — asks about policy, future trends, or recommendations related to a broader issue

For CEFR {scenario['level']}:
{'- Use simple vocabulary and short sentences. Questions should be very clear and concrete.' if scenario['level'] == 'A2' else ''}
{'- Use moderately complex language. Questions should require some elaboration but remain accessible.' if scenario['level'] == 'B1' else ''}
{'- Use sophisticated vocabulary. Questions should require analysis and well-supported opinions.' if scenario['level'] == 'B2' else ''}
{'- Use advanced, academic-register language. Questions should require nuanced argumentation and abstract reasoning.' if scenario['level'] == 'C1' else ''}

Each question's text should be 1-3 sentences long for Q1-Q2, and 2-4 sentences for Q3-Q4 (providing more context to argue with).
Each question has a timeLimit of 45 seconds.

JSON schema:
{{
  "topic": "{scenario['topic']}",
  "scenario": "{scenario['scenario']}",
  "questions": [
    {{"number": 1, "type": "Personal Experience", "text": "...", "audioUrl": "placeholder", "timeLimit": 45}},
    {{"number": 2, "type": "Personal Reaction", "text": "...", "audioUrl": "placeholder", "timeLimit": 45}},
    {{"number": 3, "type": "Opinion", "text": "...", "audioUrl": "placeholder", "timeLimit": 45}},
    {{"number": 4, "type": "Prediction/Recommendation", "text": "...", "audioUrl": "placeholder", "timeLimit": 45}}
  ]
}}

Output ONLY the raw JSON object. No markdown. No commentary."""


SYSTEM_PROMPT = f"""You are an ETS-certified Language Assessment Designer for the TOEFL 2026 Speaking section.
Follow the RR-25-12 spec for Take an Interview items.
Interview questions must progress from factual to opinion-based. Topics must be accessible without specialized knowledge.
Questions must provide natural conversational cues.

MANUAL EXCERPT:
{manual_text}
"""


def generate_interview(scenario, max_retries=3):
    prompt = build_prompt(scenario)
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt],
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.8,
                )
            )
            match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if not match:
                print(f"    [attempt {attempt+1}] No JSON found")
                continue
            data = json.loads(match.group(0))
            qs = data.get("questions", [])
            if len(qs) != 4:
                print(f"    [attempt {attempt+1}] Expected 4 questions, got {len(qs)}")
                continue
            return data
        except Exception as e:
            print(f"    [attempt {attempt+1}] Error: {e}")
            time.sleep(5)
    return None


def run():
    db = SessionLocal()

    # Check which topics already exist
    existing = db.query(TestItem).filter(TestItem.task_type == TaskType.TAKE_AN_INTERVIEW).all()
    existing_topics = set()
    for item in existing:
        try:
            data = json.loads(item.prompt_content)
            existing_topics.add(data.get("topic", "").lower())
        except:
            pass

    total_added = 0

    for idx, scenario in enumerate(SCENARIOS):
        if scenario["topic"].lower() in existing_topics:
            print(f"  [{idx+1}/{len(SCENARIOS)}] Skip '{scenario['topic']}' — already exists.")
            continue

        print(f"\n  [{idx+1}/{len(SCENARIOS)}] Generating {scenario['level']} interview: {scenario['topic']}...")

        data = generate_interview(scenario)
        if not data:
            print(f"  ✗ Failed to generate '{scenario['topic']}' after retries.")
            continue

        item = TestItem(
            id=str(uuid.uuid4()),
            section=SectionType.SPEAKING,
            task_type=TaskType.TAKE_AN_INTERVIEW,
            target_level=CEFRLevel[scenario["level"]],
            irt_difficulty=scenario["diff"],
            irt_discrimination=1.0,
            prompt_content=json.dumps(data),
            is_active=True,
            lifecycle_status=ItemStatus.DRAFT,
            version=1,
            generated_by_model="gemini-2.5-flash",
            generation_notes=f"Interview: {scenario['topic']} ({scenario['level']}). 4 progressive prompts.",
        )
        db.add(item)
        db.commit()
        total_added += 1
        print(f"  ✓ Saved '{scenario['topic']}' ({scenario['level']})")

        # Brief pause to avoid rate limits
        time.sleep(2)

    db.close()
    print(f"\n{'='*60}")
    print(f"  DONE! Generated {total_added} new Interview items.")
    print(f"  Total Interview items now: {len(existing) + total_added}")
    print(f"{'='*60}")


if __name__ == "__main__":
    run()
