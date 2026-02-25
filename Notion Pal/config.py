"""
Configuration for the Autonomous Notion Transcript Agent.
All database IDs point to the mock databases under Page A (AntiGravity).
"""

# ── Page A (AntiGravity) ──────────────────────────────────────────────
PAGE_A_ID = "3115eb7b-e7e4-807d-8693-e40d2cd508db"

# ── Database IDs (mock databases under Page A) ────────────────────────
TRIGGER_DB = "9c019132-bbca-4e32-a33f-559dcc45f3b8"   # 教学逐字稿记录 (poll source)
SCHEDULE_DB = "5576ad60-3cf2-4ada-bdd6-af1a09f2e645"   # 小楷课表 (Phase 1 target)
QUALITY_DB = "d52d82bc-9e3f-48fb-bbb7-eef86da455f7"    # 教学质量跟踪 (Phase 3 target)
TRACKING_DB = "3ca87a8d-124f-4946-b0a9-9d9958c5d466"   # 学情记录 (Phase 4 target)

# ── Status values for 清洗状态 ────────────────────────────────────────
STATUS_PENDING = "待清洗"
STATUS_PROCESSING = "清洗中"
STATUS_DONE = "已清洗"

# ── Polling configuration ─────────────────────────────────────────────
POLL_INTERVAL_SECONDS = 30

# ── Phase 1: Output module structure (10 modules from v3 prompt) ──────
PHASE1_MODULES = [
    "页面头部",          # Header: student name, highlights
    "一、本节课用了哪些材料",  # Materials used
    "二、学生课堂输出",      # Student output / exercises
    "三、老师示范 + 重点词汇", # Teacher demo + key vocabulary
    "四、本节课纠错",        # Error correction table
    "四½、定稿作文",        # Final essay (writing class only)
    "五、课后任务",          # Homework assignments
    "六、老师金句",          # Teacher quotes
    "七、学习心态分析",      # Learning mindset analysis
    "八、补充词汇",          # Supplementary vocabulary
    "九、其他补充内容",      # Additional content
    "十、方法总结",          # Method summary
]

# ── Gemini prompt for transcript processing ───────────────────────────
GEMINI_SYSTEM_PROMPT = """你是一个专业的教学逐字稿分析助手。你的任务是将课堂逐字稿整理成结构化的课堂笔记。

请根据逐字稿内容，输出以下JSON格式的结构化数据：

```json
{
  "student_name": "学生姓名",
  "highlights": "本次课亮点表现（1-3句话）",
  "materials": [
    {"name": "材料名称", "description": "简短说明"}
  ],
  "student_output": [
    {
      "exercise_name": "练习名称",
      "student_answer": "学生的回答/作文原文",
      "other_students": "其他同学思路（如有）"
    }
  ],
  "teacher_demo": [
    {
      "template_name": "段落/模板名称",
      "full_text": "完整示范文本",
      "vocabulary_upgrades": [
        {"basic": "普通词", "advanced": "高级词", "level": "如A1→C1"}
      ]
    }
  ],
  "error_corrections": [
    {
      "original": "原句",
      "error_type": "错误类型",
      "correction": "修正",
      "rule": "规则说明",
      "similar_examples": "同类易错",
      "memory_tip": "记忆技巧"
    }
  ],
  "final_essay": "定稿作文全文（仅写作课，否则为null）",
  "homework": [
    "任务1描述",
    "任务2描述"
  ],
  "teacher_quotes": [
    "引用老师原话1",
    "引用老师原话2"
  ],
  "mindset_analysis": {
    "engagement": "课堂参与度描述",
    "confidence": "自信心描述",
    "patterns": "行为模式描述",
    "emotional_state": "情绪状态描述"
  },
  "supplementary_vocab": [
    {"word": "生词", "meaning": "释义", "example": "例句"}
  ],
  "additional_content": [
    "补充内容1（如有）"
  ],
  "method_summary": [
    {
      "name": "方法名称",
      "when_to_use": "什么时候用",
      "how_to": "怎么操作",
      "example": "举例",
      "caution": "注意点"
    }
  ],
  "teaching_quality": {
    "highlights": "教学亮点（精彩瞬间、有效互动、生动类比）",
    "improvements": "待改进之处（偏离主题、冗余讲解、时间分配）",
    "language_errors": [
      {"error": "错误内容", "correction": "正确表达", "context": "上下文"}
    ],
    "scores": {
      "内容覆盖度": "A/B/C/D",
      "学生参与度": "A/B/C/D",
      "纠错有效性": "A/B/C/D",
      "时间管理": "A/B/C/D"
    }
  },
  "student_tracking": {
    "skills_progress": "技能进步与弱项",
    "exam_plans": "考试安排（如有提及）",
    "mental_state": "精神状态评估",
    "positive_notes": ["正面观察1", "正面观察2"],
    "negative_notes": ["负面观察1"]
  }
}
```

要求：
1. 金句至少提取5-8句，包括对学生的评价、方法论讲解、激励性话语、幽默表达
2. 方法至少提取3-6个，包括审题方法、关键词回应、话题框架、行文结构、衔接词用法
3. 保留老师的口语风格，不要过度书面化
4. 如果某个模块在逐字稿中没有对应内容，用空数组或null表示
5. 四½定稿作文模块仅在写作课中输出
6. 纠错表必须包含所有在课堂中发现的错误
"""
