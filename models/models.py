import enum
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class MemberTypes(str, enum.Enum):
    FREE = "FREE"
    PRO = "PRO"
    AMATEUR = "AMATEUR"
    JUNIOR = "JUNIOR"
    LIFE = "LIFE"
    HONORARY = "HONORARY"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class Membership(Base):
    """
    Prisma: memberships
    Defined first because users holds a FK to memberships.
    """
    __tablename__ = "memberships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nzdg_number = Column(Integer, autoincrement=True, nullable=False, unique=True)
    payment_status = Column(String(20), nullable=False)           # e.g. 'paid', 'pending', 'failed'
    payment_date = Column(DateTime, nullable=True)
    membership_expiration = Column(DateTime, nullable=True)
    membership_type = Column(
        Enum(MemberTypes, name="member_types"),
        nullable=False,
        default=MemberTypes.FREE,
    )

    # Relationships
    users = relationship("User", back_populates="membership")

    __table_args__ = (
        Index("ix_memberships_id_nzdg_number", "id", "nzdg_number"),
    )


class User(Base):
    """Prisma: users"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kinde_id = Column(String(255), nullable=True)
    given_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=True)
    email = Column(String, unique=True, nullable=True)
    pdga_number = Column(Integer, unique=True, nullable=True)
    division = Column(String(4), nullable=True)
    address = Column(String(255), nullable=True)

    membership_id = Column(UUID(as_uuid=True), ForeignKey("memberships.id"), nullable=True)

    # Relationships
    membership = relationship("Membership", back_populates="users")
    points_ledger = relationship("PointsLedger", back_populates="users")
    tour_results = relationship("TourResult", back_populates="users")
    round_rating = relationship("RoundRating", back_populates="users")

    __table_args__ = (
        Index("ix_users_id_pdga_number", "id", "pdga_number"),
        Index("ix_users_kinde_id", "kinde_id"),
        Index("ix_users_membership_id", "membership_id"),
    )


class Tour(Base):
    """Prisma: tour"""
    __tablename__ = "tour"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    # Relationships
    tour_events = relationship("TourEvent", back_populates="tour")
    points_ledger = relationship("PointsLedger", back_populates="tour")
    tour_results = relationship("TourResult", back_populates="tour")
    round_rating = relationship("RoundRating", back_populates="tour")


class TourEvent(Base):
    """Prisma: tour_events"""
    __tablename__ = "tour_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    order = Column(Integer, nullable=False)
    points = Column(Integer, nullable=False)
    url = Column(String(255), nullable=False)
    major = Column(Boolean, nullable=False)
    event_type = Column(String, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    tier = Column(String, nullable=True)
    location = Column(String(255), nullable=True)
    island = Column(String(3), nullable=True)

    tour_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tour.id", ondelete="NO ACTION", onupdate="NO ACTION"),
        nullable=False,
    )

    # Relationships
    tour = relationship("Tour", back_populates="tour_events")
    tour_results = relationship("TourResult", back_populates="tour_events")
    round_rating = relationship("RoundRating", back_populates="tour_events")

    __table_args__ = (
        Index("ix_tour_events_tour_id", "tour_id"),
    )


class TourResult(Base):
    """Prisma: tour_results"""
    __tablename__ = "tour_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    tour_event_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tour_events.id", ondelete="NO ACTION", onupdate="NO ACTION"),
        nullable=False,
    )
    division = Column(String(4), nullable=False)
    place = Column(Integer, nullable=False)
    points = Column(Integer, nullable=False)
    tour_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tour.id", ondelete="NO ACTION", onupdate="NO ACTION"),
        nullable=False,
    )
    membership_type = Column(
        Enum(MemberTypes, name="member_types"),
        nullable=False,
        default=MemberTypes.FREE,
    )

    # Relationships
    users = relationship("User", back_populates="tour_results")
    tour_events = relationship("TourEvent", back_populates="tour_results")
    tour = relationship("Tour", back_populates="tour_results")
    round_ratings = relationship("RoundRating", back_populates="tour_results")

    __table_args__ = (
        Index("ix_tour_results_player_id", "player_id"),
        Index("ix_tour_results_tour_event_id", "tour_event_id"),
        Index("ix_tour_results_membership_type", "membership_type"),
        Index("ix_tour_results_tour_id", "tour_id"),
    )


class RoundRating(Base):
    """Prisma: round_rating"""
    __tablename__ = "round_rating"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    tour_event_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tour_events.id", ondelete="NO ACTION", onupdate="NO ACTION"),
        nullable=False,
    )
    round = Column(Integer, nullable=False)
    rating = Column(Integer, nullable=False)
    tour_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tour.id", ondelete="NO ACTION", onupdate="NO ACTION"),
        nullable=False,
    )
    tour_results_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tour_results.id"),
        nullable=True,
    )

    # Relationships
    users = relationship("User", back_populates="round_rating")
    tour_events = relationship("TourEvent", back_populates="round_rating")
    tour_results = relationship("TourResult", back_populates="round_ratings")
    tour = relationship("Tour", back_populates="round_rating")

    __table_args__ = (
        Index("ix_round_rating_player_id", "player_id"),
        Index("ix_round_rating_tour_event_id", "tour_event_id"),
        Index("ix_round_rating_tour_id", "tour_id"),
    )


class PointsLedger(Base):
    """Prisma: points_ledger"""
    __tablename__ = "points_ledger"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    division = Column(String(5), nullable=False)
    total_points = Column(Integer, nullable=False)

    # JSON fields: {event_id: points, ...}
    event_points = Column(JSON, nullable=False)                   # events counted toward total
    all_events_played_and_points = Column(JSON, nullable=False)   # all events for display

    tour_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tour.id", ondelete="NO ACTION", onupdate="NO ACTION"),
        nullable=False,
    )

    # Relationships
    users = relationship("User", back_populates="points_ledger")
    tour = relationship("Tour", back_populates="points_ledger")

    __table_args__ = (
        Index("ix_points_ledger_player_id", "player_id"),
        Index("ix_points_ledger_tour_id", "tour_id"),
        Index("ix_points_ledger_player_id_division", "player_id", "division"),
    )


class FeatureFlag(Base):
    """Prisma: feature_flags"""
    __tablename__ = "feature_flags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)       # e.g. "user_membership_enabled"
    description = Column(String(255), nullable=True)
    enabled = Column(Boolean, nullable=False)
    environment = Column(String(50), nullable=False)              # e.g. "staging", "production"

    __table_args__ = (
        Index("ix_feature_flags_name_environment", "name", "environment"),
    )