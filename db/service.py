import uuid
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete

from db.models import EnrollmentUser, EnrollmentStatus
from utils.logger import get_logger

logger = get_logger(__name__)


class EnrollmentService:

    # CREATE
    @staticmethod
    def create_enrollment(
        db:            Session,
        name:          str,
        email:         str,
        address:       str,
        qualification: str,
        course:        str,
    ) -> EnrollmentUser:
        """Insert a new enrollment record with status = PENDING."""

        record = EnrollmentUser(
            name          = name,
            email         = email,
            address       = address,
            qualification = qualification,
            course        = course,
            status        = EnrollmentStatus.PENDING,
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        logger.info(f"[Service] Enrollment created — id={record.id} | course={record.course}")
        return record


    # READ — single by ID 
    @staticmethod
    def get_enrollment_by_id(
        db:            Session,
        enrollment_id: uuid.UUID,
    ) -> Optional[EnrollmentUser]:
        """Fetch one enrollment by UUID primary key. Returns None if not found."""

        stmt   = select(EnrollmentUser).where(EnrollmentUser.id == enrollment_id)
        record = db.execute(stmt).scalar_one_or_none()

        if not record:
            logger.warning(f"[Service] Not found — id={enrollment_id}")

        return record


    # READ — by email 
    @staticmethod
    def get_enrollments_by_email(
        db:    Session,
        email: str,
    ) -> List[EnrollmentUser]:
        """Return all enrollments for a given email address."""

        stmt    = select(EnrollmentUser).where(EnrollmentUser.email == email)
        records = db.execute(stmt).scalars().all()

        logger.info(f"[Service] Found {len(records)} enrollment(s) for email={email}")
        return records


    # READ — all 
    @staticmethod
    def get_all_enrollments(
        db:     Session,
        limit:  int = 100,
        offset: int = 0,
    ) -> List[EnrollmentUser]:
        """Return a paginated list of all enrollments, newest first."""

        stmt    = (
            select(EnrollmentUser)
            .order_by(EnrollmentUser.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        records = db.execute(stmt).scalars().all()

        logger.info(f"[Service] Fetched {len(records)} enrollment(s)")
        return records


    # UPDATE — partial 
    @staticmethod
    def update_enrollment(
        db:            Session,
        enrollment_id: uuid.UUID,
        **fields,
    ) -> Optional[EnrollmentUser]:
        """
        Partially update an enrollment. Pass only the fields you want to change.

        Example:
            EnrollmentService.update_enrollment(db, record_id, email="new@mail.com")
        """
        if not fields:
            logger.warning("[Service] update_enrollment called with no fields.")
            return EnrollmentService.get_enrollment_by_id(db, enrollment_id)

        # Map string status  enum if provided
        if "status" in fields:
            fields["status"] = EnrollmentStatus(fields["status"])

        stmt   = (
            update(EnrollmentUser)
            .where(EnrollmentUser.id == enrollment_id)
            .values(**fields)
            .returning(EnrollmentUser)
        )
        result = db.execute(stmt).scalar_one_or_none()

        if not result:
            logger.warning(f"[Service] update_enrollment — not found id={enrollment_id}")
            return None

        db.commit()
        db.refresh(result)

        logger.info(f"[Service] Updated — id={enrollment_id} | fields={list(fields.keys())}")
        return result


    # UPDATE — confirm 
    @staticmethod
    def confirm_enrollment(
        db:            Session,
        enrollment_id: uuid.UUID,
    ) -> Optional[EnrollmentUser]:
        """Set status = CONFIRMED."""
        return EnrollmentService.update_enrollment(
            db, enrollment_id, status=EnrollmentStatus.CONFIRMED.value
        )


    # UPDATE — cancel 
    @staticmethod
    def cancel_enrollment(
        db:            Session,
        enrollment_id: uuid.UUID,
    ) -> Optional[EnrollmentUser]:
        """Set status = CANCELLED."""
        return EnrollmentService.update_enrollment(
            db, enrollment_id, status=EnrollmentStatus.CANCELLED.value
        )


    # DELETE 
    @staticmethod
    def delete_enrollment(
        db:            Session,
        enrollment_id: uuid.UUID,
    ) -> bool:
        """
        Permanently delete an enrollment record.
        Returns True if deleted, False if not found.
        """
        stmt   = delete(EnrollmentUser).where(EnrollmentUser.id == enrollment_id)
        result = db.execute(stmt)
        db.commit()

        deleted = result.rowcount > 0
        if deleted:
            logger.info(f"[Service] Deleted — id={enrollment_id}")
        else:
            logger.warning(f"[Service] delete_enrollment — not found id={enrollment_id}")

        return deleted