from datetime import datetime

import streamlit as st

from database import get_db
from models.models import Tour, TourEvent

def get_all_tours() -> list[dict]:
    """Fetch all tours ordered by most recent first."""
    with get_db() as session:
        tours = (
            session.query(Tour)
            .order_by(Tour.start_date.desc())
            .all()
        )
        return [{"id": str(t.id), "name": t.name, "start_date": t.start_date, "end_date": t.end_date} for t in tours]


def get_active_tour_id(tours: list[dict]) -> str | None:
    """Return the id of the first currently active tour."""
    today = datetime.now()
    for tour in tours:
        if tour["start_date"] <= today <= tour["end_date"]:
            return tour["id"]
    return tours[0]["id"] if tours else None


def get_events_for_tour(tour_id: str) -> list[TourEvent]:
    """Fetch all events for a tour ordered by event order."""
    with get_db() as session:
        events = (
            session.query(TourEvent)
            .filter_by(tour_id=tour_id)
            .order_by(TourEvent.order)
            .all()
        )
        session.expunge_all()  # cleanly detach all objects from session
        return events


# --- Main ---
st.title("Tour Events")

all_tours = get_all_tours()

if not all_tours:
    st.warning("No tours found.")
else:
    tour_options = {t["id"]: t["name"] for t in all_tours}
    default_tour_id = get_active_tour_id(all_tours)
    default_index = list(tour_options.keys()).index(default_tour_id) if default_tour_id else 0

    selected_tour_id = st.selectbox(
        "Select Tour",
        options=list(tour_options.keys()),
        format_func=lambda x: tour_options[x],
        index=default_index,
    )

    selected_tour = next(t for t in all_tours if t["id"] == selected_tour_id)

    # Tour date range badge
    start = selected_tour["start_date"].strftime("%d %b %Y")
    end = selected_tour["end_date"].strftime("%d %b %Y")
    st.caption(f"{start} — {end}")

    st.divider()

    events = get_events_for_tour(selected_tour_id)

    if not events:
        st.info("No tournaments added for this tour yet.")
    else:
        for event in events:
            with st.container():
                col1, col2 = st.columns([3, 1])

                with col1:
                    title = f"{event.name}" if event.major else event.name
                    st.subheader(title)
                    if event.location:
                        st.caption(f"{event.location}")
                    if event.start_date and event.end_date:
                        e_start = event.start_date.strftime("%d %b %Y")
                        e_end = event.end_date.strftime("%d %b %Y")
                        st.caption(f"{e_start} — {e_end}")
                    st.write(f"[{event.url}]({event.url})")

                with col2:
                    st.metric("Points", event.points)
                    if event.major:
                        st.success("Major")
                    if event.tier:
                        st.caption(f"Tier: {event.tier}")

            st.divider()