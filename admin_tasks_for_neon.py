import uuid

import httpx
import streamlit as st
from sqlalchemy import func
from sqlalchemy.orm import Session

from models.models import TourEvent, PointsLedger, RoundRating, TourResult, User
from trigger_tournament_added import trigger_tournament_added, _update_points_ledger


def add_tournament_and_players(session: Session, name: str, url: str,
                               points: int, major: bool, order: int, tour_id: str):
    # will add a tournament and trigger the points to be calculated
    event = TourEvent(
        id=uuid.uuid4(),
        name=name,
        url=url,
        points=points,
        major=major,
        order=order,
        tour_id=tour_id,
    )
    session.add(event)
    print(f"Added tournament {name} with ID {event.id} to the database.")
    # need to trigger the tigger.dev to add points to players who have this tournament in their points ledger
    trigger_tournament_added(session,
                             {
                                 "event_id": str(event.id),
                                 "name": name,
                                 "url": url,
                                 "points": points,
                                 "major": major,
                                 "order": order,
                                 "tour_id": tour_id,
                             }
                             )

    session.commit()


def rearrange_tournament_order(session: Session, sorted_ids: list[str]):
    for i, event_id in enumerate(sorted_ids):
        event = session.query(TourEvent).filter_by(id=event_id).first()
        if event:
            event.order = i + 1
    session.commit()


def remove_tournament_and_player_points(session: Session, event_id: str):
    print(f"Removing tournament with ID {event_id} and associated player points.")
    session.query(RoundRating).filter_by(tour_event_id=event_id).delete()
    session.query(TourResult).filter_by(tour_event_id=event_id).delete()
    session.query(TourEvent).filter_by(id=event_id).delete()

    # Recalculate the total points for all players who had points from this tournament
    affected_ledgers = session.query(PointsLedger).filter(
        PointsLedger.event_points[str(event_id)].isnot(None)
    ).all()

    ledgers_to_update = []

    for ledger in affected_ledgers:
        # Get all remaining tour results for this player and tour
        all_tour_results = session.query(TourResult).filter(
            TourResult.player_id == ledger.player_id,
            TourResult.tour_id == ledger.tour_id,
            TourResult.division == ledger.division,
            TourResult.tour_event_id != event_id  # ← exclude by id
        ).all()
        points_ledger_entry = _update_points_ledger(
            ledger, all_tour_results
        )
        if points_ledger_entry:
            ledgers_to_update.append(points_ledger_entry)

    # Doubly

    session.commit()

    remaining = session.query(PointsLedger).filter(
        PointsLedger.event_points[str(event_id)].isnot(None)
    ).all()

    assert len(remaining) == 0, f"Found {len(remaining)} ledgers still containing event {event_id}"

    # go through and make sure ledgers with 0 points are removed
    zero_point_ledgers = session.query(PointsLedger).filter(PointsLedger.total_points <= 0).all()
    for ledger in zero_point_ledgers:
        print(f"Deleting zero-point ledger for player {ledger.player_id} in tour {ledger.tour_id}")
        session.delete(ledger)
    session.commit()

    # Remove all users that now have no points ledgers (i.e. they only had points from this tournament)
    zero_point_users = session.query(PointsLedger.player_id).group_by(PointsLedger.player_id).having(
        func.sum(PointsLedger.total_points) <= 0).all()
    for user_id, in zero_point_users:
        print(f"Deleting user {user_id} with no remaining points")
        session.query(User).filter_by(id=user_id).delete()
    session.commit()
    print(
        f"Finished removing tournament {event_id} and associated points. Deleted {len(zero_point_ledgers)} zero-point ledgers and {len(zero_point_users)} users with no remaining points.")


def _trigger_task(task_id: str, payload: dict):
    """Internal helper to call trigger.dev REST API."""
    response = httpx.post(
        f"https://api.trigger.dev/api/v1/tasks/{task_id}/trigger",
        headers={
            "Authorization": f"Bearer {st.secrets['TRIGGER_API_KEY']}",
            "Content-Type": "application/json",
        },
        json={"payload": payload},
    )
    if response.status_code != 200:
        raise Exception(f"Trigger.dev error: {response.status_code} - {response.text}")
    return response.json()
