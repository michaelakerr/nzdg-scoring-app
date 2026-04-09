import uuid
from datetime import datetime

import pandas as pd
import streamlit as st

from database import get_session_factory
from models.models import Tour, TourEvent, TourResult, User, PointsLedger

SessionFactory = get_session_factory()

DIVISION_ORDER = [
    "MPO",
    "FPO",
    "MP40", "MP50",
    "MA1",
    "FA1", "FA2", "FA3", "FA4",
    "MA2",
    "MA3", "MA4",
    "MA40",
    "FP40", "FA40",
    "MA50",
    "FA50", "FP50",
    "MA60", "MP60",
    "FA60", "FP60",
    "MA70", "MP70",
    "FA70", "FP70",
    "MJ18", "MJ15", "MJ12", "MJ10", "MJ08", "MJ06",
    "FJ18", "FJ15", "FJ12", "FJ10", "FJ08", "FJ06",
]


def get_all_tours() -> list[dict]:
    """Fetch all tours ordered by most recent first."""
    with SessionFactory() as session:
        tours = (
            session.query(Tour)
            .order_by(Tour.start_date.desc())
            .all()
        )
        return [
            {
                "id": str(t.id),
                "name": t.name,
                "start_date": t.start_date,
                "end_date": t.end_date,
            }
            for t in tours
        ]


def get_active_tour_id(tours: list[dict]) -> str | None:
    """Return the id of the first currently active tour."""
    today = datetime.now()
    for tour in tours:
        if tour["start_date"] <= today <= tour["end_date"]:
            return tour["id"]
    return tours[0]["id"] if tours else None


def get_divisions_for_tour(tour_id: str) -> list[str]:
    """Fetch all distinct divisions that exist in the tour."""
    with SessionFactory() as session:
        rows = (
            session.query(TourResult.division)
            .filter(TourResult.tour_id == uuid.UUID(tour_id))
            .distinct()
            .order_by(TourResult.division)
            .all()
        )

        rows_to_divs = [row.division for row in rows]

        return sorted(rows_to_divs,
                      key=lambda d: DIVISION_ORDER.index(d) if d in DIVISION_ORDER else len(DIVISION_ORDER))


def get_tournament_events_for_tour(tour_id: str) -> list[dict]:
    """Fetch all tour events ordered by event order."""
    with SessionFactory() as session:
        events = (
            session.query(TourEvent)
            .filter_by(tour_id=uuid.UUID(tour_id))
            .order_by(TourEvent.order)
            .all()
        )
        return [{"id": str(e.id), "name": e.name} for e in events]


def get_results_for_division(tour_id: str, division: str) -> pd.DataFrame | None:
    """Fetch standings for a division from the PointsLedger table.
    Returns a tuple of (data_df, highlight_df) where highlight_df marks counted events green.
    """
    events = get_tournament_events_for_tour(tour_id)
    if not events:
        return None

    with SessionFactory() as session:
        rows = (
            session.query(
                User.pdga_number,
                User.given_name,
                User.last_name,
                PointsLedger.total_points,
                PointsLedger.event_points,
                PointsLedger.all_events_played_and_points,
            )
            .join(User, PointsLedger.player_id == User.id)
            .filter(
                PointsLedger.tour_id == uuid.UUID(tour_id),
                PointsLedger.division == division,
            )
            .all()
        )

    if not rows:
        return None

    event_id_to_name = {e["id"]: e["name"] for e in events}
    event_columns = [e["name"] for e in events]

    records = []

    for pdga_number, given_name, last_name, total_points, event_points, all_events in rows:
        record = {
            "pdga_number": pdga_number,
            "name": f"{given_name} {last_name}",
            "total_points": total_points,

        }

        counted_event_ids = set((event_points or {}).keys())

        for event_id, points in (all_events or {}).items():
            event_name = event_id_to_name.get(event_id)
            if event_name:
                record[event_name] = points

        records.append(record)

    df = pd.DataFrame(records)

    # Ensure all event columns exist
    for col in event_columns:
        if col not in df.columns:
            df[col] = None

    df = df.sort_values("total_points", ascending=False).reset_index(drop=True)
    df["place"] = df["total_points"].rank(ascending=False, method="min").astype(int)

    cols = ["place", "pdga_number", "name", "total_points"] + event_columns
    return df[cols]


def build_column_config(event_columns: list[str]) -> dict:
    config = {
        "place": st.column_config.NumberColumn("Place", width="small"),
        "pdga_number": st.column_config.NumberColumn("PDGA #", width="small", format="%.0f"),
        "name": st.column_config.TextColumn("Player", width="medium"),
        "total_points": st.column_config.NumberColumn("Total Points", format="%.2f", width="small"),
    }
    for col in event_columns:
        config[col] = st.column_config.NumberColumn(col, format="%.2f", width="small")
    return config


# --- Main ---
st.title("Tour Standings")

all_tours = get_all_tours()

if not all_tours:
    st.warning("No tours found.")
else:
    tour_options = {t["id"]: t["name"] for t in all_tours}
    default_tour_id = get_active_tour_id(all_tours)
    default_index = list(tour_options.keys()).index(default_tour_id) if default_tour_id else 0

    left, right = st.columns([1, 1])
    with left:
        selected_tour_id = st.selectbox(
            "Select Tour",
            options=list(tour_options.keys()),
            format_func=lambda x: tour_options[x],
            index=default_index,
        )

        selected_tour = next(t for t in all_tours if t["id"] == selected_tour_id)
        start = selected_tour["start_date"].strftime("%d %b %Y")
        end = selected_tour["end_date"].strftime("%d %b %Y")
        st.caption(f"{start} — {end}")

    divisions = get_divisions_for_tour(selected_tour_id)

    with right:

        if not divisions:
            st.info("No results have been entered for this tour yet.")

        selected = st.selectbox(
            "Select Division",
            options=[""] + divisions,
            format_func=lambda x: "— choose a division —" if x == "" else x
        )
        if selected:
            st.session_state["selected_division"] = selected
            st.session_state["selected_tour_id_standings"] = selected_tour_id

    if (
            "selected_division" in st.session_state
            and "selected_tour_id_standings" in st.session_state
            and st.session_state["selected_tour_id_standings"] == selected_tour_id
    ):
        division = st.session_state["selected_division"]

        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(f"{division} Standings")
        with col2:
            if st.button("✕ Clear", key="clear_division"):
                del st.session_state["selected_division"]
                del st.session_state["selected_tour_id_standings"]
                st.rerun()

        result = get_results_for_division(selected_tour_id, division)
        if result is not None:
            df = result
            event_cols = [
                c for c in df.columns
                if c not in ["place", "pdga_number", "name", "total_points"]
            ]
            st.dataframe(
                df,
                hide_index=True,
                width="stretch",
                height=600,
                column_config=build_column_config(event_cols),
            )
            st.caption(f"{len(df)} players • {len(event_cols)} events")
        else:
            st.success("No results yet for this division.")
    else:
        st.success("Select a division to view standings.")
