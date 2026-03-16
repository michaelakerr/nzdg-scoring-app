import uuid
import streamlit as st
import httpx
from sqlalchemy.orm import Session

from models.models import TourEvent, PointsLedger


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
    # need to trigger the tigger.dev to add points to players who have this tournament in their points ledger
    _trigger_task(
        "trigger_tournament_added", # to be abstracted
        {
            "event_id": str(event.id),
            "name": name,
            "url": url,
            "points": points,
            "major": major,
            "order": order,
            "tour_id": tour_id,
        },
    )

    session.commit()


def rearrange_tournament_order(session: Session, sorted_ids: list[str]):
    for i, event_id in enumerate(sorted_ids):
        event = session.query(TourEvent).filter_by(id=event_id).first()
        if event:
            event.order = i + 1
    session.commit()


def remove_tournament_and_player_points(session: Session, event_id: str):
    # Remove associated ledger entries first, then the event
    session.query(PointsLedger).filter_by(tour_event_id=event_id).delete()
    session.query(TourEvent).filter_by(id=event_id).delete()
    session.commit()

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