import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class GameSessionStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    GUESSED_CORRECT = "guessed_correct"
    GUESSED_INCORRECT = "guessed_incorrect"
    ABANDONED = "abandoned"


class GameAnswerValue(str, enum.Enum):
    YES = "yes"
    PROBABLY_YES = "probably_yes"
    DONT_KNOW = "dont_know"
    PROBABLY_NO = "probably_no"
    NO = "no"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    sessions: Mapped[list["GameSession"]] = relationship(back_populates="user")


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    times_guessed_correctly: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    times_guessed_incorrectly: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    answers: Mapped[list["CharacterAnswer"]] = relationship(back_populates="character")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    text: Mapped[str] = mapped_column(String(512), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    times_asked: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_information_gain: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    answers: Mapped[list["CharacterAnswer"]] = relationship(back_populates="question")


class CharacterAnswer(Base):
    __tablename__ = "character_answers"
    __table_args__ = (
        UniqueConstraint("character_id", "question_id", name="uq_character_question"),
        CheckConstraint("likelihood >= 0.0 AND likelihood <= 1.0", name="ck_likelihood_range"),
        CheckConstraint("sample_size >= 0", name="ck_sample_size_nonneg"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    character_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("characters.id"), nullable=False)
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("questions.id"), nullable=False)
    likelihood: Mapped[float] = mapped_column(Float, nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    character: Mapped["Character"] = relationship(back_populates="answers")
    question: Mapped["Question"] = relationship(back_populates="answers")


class GameSession(Base):
    __tablename__ = "game_sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    status: Mapped[GameSessionStatus] = mapped_column(
        Enum(GameSessionStatus, name="game_session_status"),
        default=GameSessionStatus.IN_PROGRESS,
        nullable=False,
    )
    guessed_character_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("characters.id"), nullable=True
    )
    actual_character_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("characters.id"), nullable=True
    )
    questions_asked_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_activity_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User | None"] = relationship(back_populates="sessions")
    answers: Mapped[list["GameAnswer"]] = relationship(back_populates="session")
    rejected_guesses: Mapped[list["RejectedGuess"]] = relationship(back_populates="session")


class RejectedGuess(Base):
    """Characters the user rejected during a session. Persisted so session
    rehydration can re-exclude them from the candidate pool after cache loss."""

    __tablename__ = "rejected_guesses"
    __table_args__ = (
        UniqueConstraint("session_id", "character_id", name="uq_session_rejected_character"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("game_sessions.id"), nullable=False)
    character_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("characters.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped["GameSession"] = relationship(back_populates="rejected_guesses")


class GameAnswer(Base):
    __tablename__ = "game_answers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("game_sessions.id"), nullable=False)
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("questions.id"), nullable=False)
    answer: Mapped[GameAnswerValue] = mapped_column(
        Enum(GameAnswerValue, name="game_answer_value"), nullable=False
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    entropy_before: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped["GameSession"] = relationship(back_populates="answers")
