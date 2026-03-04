import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector

from db.database import Base


# Enrollment Status Enum 
import enum

class EnrollmentStatus(str, enum.Enum):
    PENDING   = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


# EnrollmentUser Model 
class EnrollmentUser(Base):
    """
    Stores every course enrollment created through CourseBot.

    Columns
    -------
    id              — UUID primary key (auto-generated)
    name            — Full name of the student
    email           — Email address (unique per enrollment attempt)
    address         — Residential address
    qualification   — Highest educational qualification
    course          — Course ID / name enrolled in
    status          — pending | confirmed | cancelled
    embedding       — 1536-dim pgvector column (reserved for future semantic search)
    created_at      — UTC timestamp of record creation
    updated_at      — UTC timestamp of last update
    """

    __tablename__ = "enrollment_users"

    # Primary Key 
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        index=True,
        comment="Auto-generated UUID primary key",
    )

    # Enrollment Fields 
    name = Column(
        String(255),
        nullable=False,
        comment="Full name of the student",
    )

    email = Column(
        String(320),           
        nullable=False,
        index=True,
        comment="Student email address",
    )

    address = Column(
        String(1000),
        nullable=False,
        comment="Residential address",
    )

    qualification = Column(
        String(500),
        nullable=False,
        comment="Highest educational qualification",
    )

    course = Column(
        String(255),
        nullable=False,
        comment="Course ID or name (e.g. genai_beginner)",
    )

    # Status 
    status = Column(
        SAEnum(EnrollmentStatus, name="enrollment_status_enum"),
        nullable=False,
        default=EnrollmentStatus.PENDING,
        comment="Enrollment lifecycle status",
    )

    # pgvector Embedding Column 
    embedding = Column(
        Vector(1536),
        nullable=True,
        comment="Optional vector embedding for semantic search (pgvector)",
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="UTC creation timestamp",
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="UTC last-update timestamp",
    )

    # Helper 
    def __repr__(self) -> str:
        return (
            f"<EnrollmentUser id={self.id} name={self.name!r} "
            f"course={self.course!r} status={self.status}>"
        )