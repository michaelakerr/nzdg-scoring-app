import uuid

import pytest

from database import get_session_factory, get_db
from models.models import RoundRating, TourEvent, TourResult, PointsLedger, User
from admin_tasks_for_neon import add_tournament_and_players, remove_tournament_and_player_points

URL = "https://www.pdga.com/tour/event/85604"

# This is seeded test data
EVENT_ID = "fb8663f9-2534-405c-9814-2b3522c68866"
TOUR_ID = uuid.UUID("206c92d5-62c9-4e27-9b8e-97c94f59e8ae")

PAYLOAD = {
    "event_id": EVENT_ID,
    "name": "Nationals 2025",
    "url": URL,
    "points": 70,
    "major": True,
    "order": 1,
    "tour_id": TOUR_ID
}
SessionFactory = get_session_factory()


@pytest.fixture
def session():
    """Single session for the test. Cleanup runs in a separate session after."""
    with get_db() as session:
        yield session

    # Test session is now closed — clean up in a fresh session
    with get_db() as cleanup_session:
        print("🧹 Starting cleanup...")
        cleanup_session.query(RoundRating).filter_by(tour_id=TOUR_ID).delete()

        cleanup_session.query(TourResult).filter_by(tour_id=TOUR_ID).delete()

        cleanup_session.query(PointsLedger).filter_by(tour_id=TOUR_ID).delete()

        cleanup_session.query(TourEvent).filter_by(tour_id=TOUR_ID).delete()

        cleanup_session.query(User).filter_by(user_type="TEST_USER").delete()

        cleanup_session.commit()
        print("✅ Cleanup complete")


def test_trigger_tournament_added(session):
    # --- Act ---
    add_tournament_and_players(
        session=session,
        name=PAYLOAD["name"],
        url=PAYLOAD["url"],
        points=PAYLOAD["points"],
        major=PAYLOAD["major"],
        order=PAYLOAD["order"],
        tour_id=PAYLOAD["tour_id"],
    )

    # --- Assert ---
    event = session.query(TourEvent).filter_by(tour_id=TOUR_ID).first()
    print(f"Queried TourEvent: {event}")
    assert event is not None, "TourEvent was not created"
    assert event.name == "Nationals 2025"
    assert event.tour_id == TOUR_ID

    rounds = session.query(RoundRating).filter_by(tour_event_id=event.id).all()
    assert len(rounds) > 0, "No RoundRatings were created"
    assert rounds[0].tour_id == TOUR_ID
    assert rounds[0].rating > 0


def test_tournament_deleted(session):
    # -Create
    add_tournament_and_players(
        session=session,
        name=PAYLOAD["name"],
        url=PAYLOAD["url"],
        points=PAYLOAD["points"],
        major=PAYLOAD["major"],
        order=PAYLOAD["order"],
        tour_id=PAYLOAD["tour_id"],
    )

    tour_event = session.query(TourEvent).filter_by(tour_id=TOUR_ID).first()

    # delete
    remove_tournament_and_player_points(session, tour_event.id)

    event = session.query(TourEvent).filter_by(tour_id=TOUR_ID).first()

    print(f"Queried TourEvent: {event}")
    assert event is None