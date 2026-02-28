import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Enum, DECIMAL, Integer, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database.connection import Base, UserBase

class UserRole(str, enum.Enum):
    ADMIN = 'ADMIN'
    STUDENT = 'STUDENT'
    RATER = 'RATER'
    PROCTOR = 'PROCTOR'
    ITEM_DESIGNER = 'ITEM_DESIGNER'

class SectionType(str, enum.Enum):
    READING = 'READING'
    LISTENING = 'LISTENING'
    SPEAKING = 'SPEAKING'
    WRITING = 'WRITING'

class CEFRLevel(str, enum.Enum):
    A1 = 'A1'
    A2 = 'A2'
    B1 = 'B1'
    B2 = 'B2'
    C1 = 'C1'
    C2 = 'C2'

class SessionStatus(str, enum.Enum):
    SCHEDULED = 'SCHEDULED'
    ACTIVE = 'ACTIVE'
    COMPLETED = 'COMPLETED'
    FLAGGED = 'FLAGGED'
    VOIDED = 'VOIDED'

class TaskType(str, enum.Enum):
    READ_ACADEMIC_PASSAGE = 'READ_ACADEMIC_PASSAGE'
    READ_IN_DAILY_LIFE = 'READ_IN_DAILY_LIFE'
    COMPLETE_THE_WORDS = 'COMPLETE_THE_WORDS'
    BUILD_A_SENTENCE = 'BUILD_A_SENTENCE'
    WRITE_ACADEMIC_DISCUSSION = 'WRITE_ACADEMIC_DISCUSSION'
    WRITE_AN_EMAIL = 'WRITE_AN_EMAIL'
    TAKE_AN_INTERVIEW = 'TAKE_AN_INTERVIEW'
    LISTEN_AND_REPEAT = 'LISTEN_AND_REPEAT'
    LISTEN_CHOOSE_RESPONSE = 'LISTEN_CHOOSE_RESPONSE'
    LISTEN_ACADEMIC_TALK = 'LISTEN_ACADEMIC_TALK'
    LISTEN_ANNOUNCEMENT = 'LISTEN_ANNOUNCEMENT'
    LISTEN_CONVERSATION = 'LISTEN_CONVERSATION'

class ItemStatus(str, enum.Enum):
    DRAFT = 'DRAFT'           # Initial authoring
    REVIEW = 'REVIEW'         # Internal QA / Editing
    FIELD_TEST = 'FIELD_TEST' # Trialing in live environment (unscored)
    ACTIVE = 'ACTIVE'         # Live and scoring
    SUSPENDED = 'SUSPENDED'   # Temporarily pulled due to issues
    EXPOSED = 'EXPOSED'       # Leaked or too many exposures (Practice only)
    ARCHIVED = 'ARCHIVED'     # Retired permanently

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.STUDENT)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

class TestItem(Base):
    __tablename__ = "test_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    author_id = Column(String, ForeignKey("users.id"))
    section = Column(Enum(SectionType), nullable=False)
    task_type = Column(Enum(TaskType), nullable=True)          # item subtype within section
    target_level = Column(Enum(CEFRLevel), nullable=False)
    irt_difficulty = Column(DECIMAL(5, 2), default=0.0)
    irt_discrimination = Column(DECIMAL(5, 2), default=1.0)
    prompt_content = Column(Text)
    media_url = Column(String(500))
    rubric_id = Column(String, nullable=True)
    
    # --- Lifecycle Status ---
    lifecycle_status = Column(Enum(ItemStatus), nullable=False, default=ItemStatus.DRAFT)
    is_active = Column(Boolean, default=False) # Keep for compatibility, should be True only if status is ACTIVE or FIELD_TEST
    
    # --- Version / Audit Trail ---
    version = Column(Integer, default=1, nullable=False)
    generated_by_model = Column(String(100), nullable=True)  # e.g. "gemini-1.5-pro", "Human"
    generation_notes = Column(Text, nullable=True)            # free-text QA notes
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    # --- Exposure / Burn-Rate Tracking ---
    exposure_count = Column(Integer, default=0, nullable=False)  # times served in live tests
    last_exposed_at = Column(DateTime(timezone=True), nullable=True)  # last time served
    # --- Import Traceability ---
        # --- Import Traceability ---
    source_file = Column(String(255), nullable=True)   # origin JSON filename
    source_id = Column(String(100), nullable=True)      # original ID in JSON (e.g. "NATSCI-01")

    questions = relationship("TestItemQuestion", back_populates="test_item", cascade="all, delete-orphan")

class TestItemQuestion(Base):
    """
    Holds individual gaps/blanks within a parent item (Testlet).
    Crucial for valid Item Response Theory (IRT) psychometrics where the "item" is the blank, not the paragraph.
    """
    __tablename__ = "test_item_questions"

    id = Column(String, primary_key=True, default=lambda: f"{uuid.uuid4()}")
    test_item_id = Column(String, ForeignKey("test_items.id"), nullable=False)
    question_number = Column(Integer, nullable=False)    # 1 through 10
    question_text = Column(String, nullable=True)        # The prompt for this item (for Analytics & Editor)
    question_audio_url = Column(String(500), nullable=True) # Spoken question audio
    replay_audio_url = Column(String(500), nullable=True)   # "Listen again to..." audio segment
    correct_answer = Column(String, nullable=True)       # e.g., "wind" or anchor essay for CR
    options = Column(JSON, nullable=True)                # for MCQ gaps
    is_constructed_response = Column(Boolean, default=False)
    max_score = Column(Integer, nullable=True)           # max rubric score for CR item
    irt_difficulty = Column(DECIMAL(5, 2), default=0.0)
    irt_discrimination = Column(DECIMAL(5, 2), default=1.0)
    exposure_count = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True)

    test_item = relationship("TestItem", back_populates="questions")

class TestSession(UserBase):
    __tablename__ = "test_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, index=True) # Was ForeignKey("users.id")
    proctor_id = Column(String, index=True) # Was ForeignKey("users.id")
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    status = Column(Enum(SessionStatus), default=SessionStatus.SCHEDULED)
    browser_fingerprint = Column(String(255))
    total_score = Column(Integer)

class ItemReviewLog(Base):
    """
    ETS-grade audit trail tracking exactly who reviewed an item, when, and their feedback.
    This replaces overwriting the 'generation_notes' column every time.
    """
    __tablename__ = "item_review_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    item_id = Column(String, ForeignKey("test_items.id"), nullable=False)
    stage_name = Column(String(50), nullable=False)   # e.g., "Content Agent", "Fairness Agent"
    reviewer = Column(String(100), nullable=False)    # e.g., "gemini-1.5-pro", "Human: Tengda"
    action = Column(String(20), nullable=False)       # e.g., "PASS", "FAIL"
    notes = Column(Text, nullable=True)               # e.g., "Refused: Used american baseball idiom."
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class ItemVersionHistory(Base):
    """
    Psychometric versioning. Every time the item's core prompt is modified,
    a snapshot of the old payload is saved here. Prevents muddying IRT data.
    """
    __tablename__ = "item_version_history"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    item_id = Column(String, ForeignKey("test_items.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    prompt_content = Column(Text, nullable=False)
    changed_by = Column(String(100), nullable=True)   # Who committed the change
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class TestResponse(UserBase):
    """
    Ledger for student responses, tying the TestSession to a specific TestItemQuestion.
    Holds the student's raw input, correct status, rubric score, and AI feedback.
    """
    __tablename__ = "test_responses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    # Same database so FK is allowed
    session_id = Column(String, ForeignKey("test_sessions.id"), nullable=False)
    # Different database, so remove FK constraint
    question_id = Column(String, index=True, nullable=False)
    student_raw_response = Column(Text, nullable=True)   # Written essay or S3 URL to audio
    is_correct = Column(Boolean, nullable=True)          # deterministic scoring
    rubric_score = Column(Integer, nullable=True)        # constructed response scoring
    ai_feedback = Column(JSON, nullable=True)            # JSON blob from the ScoringEngine

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("TestSession", backref="responses")
    # question = relationship("TestItemQuestion", backref="responses") # Cross-DB relationship removed


class TestEventLog(UserBase):
    """
    High-frequency ETS Audit Log. Tracks every action: keystrokes, answers, 
    blur/focus events, item rendering, and audio playback.
    """
    __tablename__ = "test_event_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("test_sessions.id"), nullable=False, index=True)
    student_id = Column(String, index=True, nullable=False) # Was ForeignKey("users.id")
    question_id = Column(String, index=True, nullable=True) # Was ForeignKey("test_item_questions.id")
    
    event_type = Column(String(50), nullable=False, index=True)
    event_data = Column(JSON, nullable=True)
    
    client_ip = Column(String(50), nullable=True)
    browser_fingerprint = Column(String(255), nullable=True)
    
    event_timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    session = relationship("TestSession", foreign_keys=[session_id])

# ──────────────────────────────────────────────────────────────────────────────
# IELTS Item Bank Models
# ──────────────────────────────────────────────────────────────────────────────

class IeltsDifficulty(str, enum.Enum):
    HIGH   = 'high'
    MEDIUM = 'medium'
    LOW    = 'low'

class IeltsPosition(str, enum.Enum):
    P1 = 'P1'
    P2 = 'P2'
    P3 = 'P3'

class IeltsPassage(Base):
    """
    One row per IELTS Reading passage (one test set = 3 passages).
    Corresponds directly to one parsed JSON file.
    """
    __tablename__ = "ielts_passages"

    id                   = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id            = Column(String(20), unique=True, nullable=False)   # e.g. "ielts-r-001"
    source_file          = Column(String(255), nullable=True)                # original PDF filename
    position             = Column(Enum(IeltsPosition), nullable=False)       # P1 / P2 / P3
    difficulty           = Column(Enum(IeltsDifficulty), nullable=True)
    title                = Column(String(500), nullable=False)
    title_cn             = Column(String(500), nullable=True)
    time_allocation      = Column(String(50), nullable=True)
    has_paragraph_labels = Column(Boolean, default=False)
    paragraphs           = Column(JSON, nullable=False)   # list of {label, text}
    question_range_start = Column(Integer, nullable=True)
    question_range_end   = Column(Integer, nullable=True)
    
    # Gold Standard Stimulus tracking
    word_count           = Column(Integer, nullable=True)
    lexile_score         = Column(DECIMAL(5, 2), nullable=True)
    topic_domain         = Column(String(255), nullable=True)
    workflow_status      = Column(Enum(ItemStatus), default=ItemStatus.DRAFT)
    
    needs_review         = Column(Boolean, default=True)
    parsed_at            = Column(DateTime(timezone=True), nullable=True)
    created_at           = Column(DateTime(timezone=True), server_default=func.now())
    updated_at           = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    question_groups      = relationship("IeltsQuestionGroup", back_populates="passage",
                                        cascade="all, delete-orphan")


class IeltsQuestionGroup(Base):
    """
    One row per question group within a passage (e.g., TFNG block, MCQ block).
    A passage usually has 2-3 groups.
    """
    __tablename__ = "ielts_question_groups"

    id            = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    passage_id    = Column(String, ForeignKey("ielts_passages.id"), nullable=False)
    group_type    = Column(String(50), nullable=False)   # TFNG, MCQ, HEADING_MATCHING, etc.
    instructions  = Column(Text, nullable=True)
    range_start   = Column(Integer, nullable=True)
    range_end     = Column(Integer, nullable=True)
    sort_order    = Column(Integer, default=0)           # position within passage

    passage       = relationship("IeltsPassage", back_populates="question_groups")
    questions     = relationship("IeltsQuestion", back_populates="group",
                                 cascade="all, delete-orphan")


class IeltsQuestion(Base):
    """
    One row per individual question.
    Decoupled from options and answer strings to support IRT metrics and partial scaffolding.
    """
    __tablename__ = "ielts_questions"

    id              = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id        = Column(String, ForeignKey("ielts_question_groups.id"), nullable=False)
    question_number = Column(Integer, nullable=False)
    question_text   = Column(Text, nullable=True)
    # Gold Standard Properties
    cognitive_skill   = Column(String(255), nullable=True)       # e.g., 'INFERENCE', 'DETAIL', 'AUTHOR_PURPOSE'
    target_cefr_level = Column(Enum(CEFRLevel), nullable=True)
    workflow_status   = Column(Enum(ItemStatus), default=ItemStatus.DRAFT)
    
    # Legacy Properties (Intact for backwards compatibility)
    options         = Column(JSON, nullable=True)      # list of {letter, text} or None
    answer          = Column(String(500), nullable=True)
    
    answer_source   = Column(String(50), nullable=True)  # "llm_generated" or "human"
    needs_review    = Column(Boolean, default=True)

    group           = relationship("IeltsQuestionGroup", back_populates="questions")
    options_list    = relationship("IeltsItemOption", back_populates="question", cascade="all, delete-orphan")
    psychometrics   = relationship("IeltsItemPsychometrics", back_populates="question", uselist=False, cascade="all, delete-orphan")


class IeltsItemOption(Base):
    """
    Stores scoring logic and distractors for each question.
    """
    __tablename__ = "ielts_item_options"

    id              = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    question_id     = Column(String, ForeignKey("ielts_questions.id"), nullable=False)
    option_text     = Column(Text, nullable=False)
    is_correct      = Column(Boolean, nullable=False, default=False)
    scoring_weight  = Column(DECIMAL(5, 2), default=1.0)
    rationale       = Column(Text, nullable=True)        # Mandatory for high-stakes audits
    distractor_type = Column(String(255), nullable=True) # E.g., 'OPPOSITE', 'NOT_GIVEN'

    question        = relationship("IeltsQuestion", back_populates="options_list")


class IeltsItemPsychometrics(Base):
    """
    Stores classical and IRT psychometric constants updated dynamically via calibration workflows.
    """
    __tablename__ = "ielts_item_psychometrics"

    question_id        = Column(String, ForeignKey("ielts_questions.id"), primary_key=True)
    
    p_value            = Column(DECIMAL(5, 3), nullable=True)
    point_biserial     = Column(DECIMAL(5, 3), nullable=True)
    
    irt_a_parameter    = Column(DECIMAL(5, 3), nullable=True)
    irt_b_parameter    = Column(DECIMAL(5, 3), nullable=True)
    irt_c_parameter    = Column(DECIMAL(5, 3), nullable=True)
    
    exposure_rate      = Column(DECIMAL(5, 3), nullable=True)
    last_calibrated_at = Column(DateTime(timezone=True), nullable=True)

    question           = relationship("IeltsQuestion", back_populates="psychometrics")


class IeltsMigrationLog(Base):
    """
    Tracks which source JSON files have been migrated. Allows safe re-runs.
    """
    __tablename__ = "ielts_migration_log"

    source_id   = Column(String(20), primary_key=True)   # e.g. "ielts-r-001"
    status      = Column(String(20), default="done")     # "done" or "error"
    error_msg   = Column(Text, nullable=True)
    migrated_at = Column(DateTime(timezone=True), server_default=func.now())
