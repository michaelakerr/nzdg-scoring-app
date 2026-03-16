import datetime
import uuid

import httpx
import streamlit as st
from sqlalchemy.orm import Session
from streamlit_sortables import sort_items

from admin_tasks_for_neon import (
    add_tournament_and_players,
    rearrange_tournament_order,
    remove_tournament_and_player_points,
)
from database import get_session_factory
from models.models import Tour, TourEvent

SessionFactory = get_session_factory()

FIREBASE_WEB_API_KEY = st.secrets["firebase_web_api_key"]
ADMIN_EMAIL = st.secrets["admin_email"]



# --- Firebase auth ---
def firebase_login(email: str, password: str) -> dict | None:
    url = (
        f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
        f"?key={FIREBASE_WEB_API_KEY}"
    )
    response = httpx.post(
        url,
        json={"email": email, "password": password, "returnSecureToken": True},
    )
    if response.status_code != 200:
        return None
    return response.json()


def verify_firebase_token(id_token: str) -> dict | None:
    url = (
        f"https://identitytoolkit.googleapis.com/v1/accounts:lookup"
        f"?key={FIREBASE_WEB_API_KEY}"
    )
    response = httpx.post(url, json={"idToken": id_token})
    if response.status_code != 200:
        return None
    users = response.json().get("users", [])
    return users[0] if users else None


# --- DB helpers ---
def get_all_tours() -> list[Tour]:
    with SessionFactory() as session:
        return session.query(Tour).order_by(Tour.start_date.desc()).all()


def get_all_tour_events(tour_id: str) -> list[TourEvent]:
    with SessionFactory() as session:
        return (
            session.query(TourEvent)
            .filter_by(tour_id=tour_id)
            .order_by(TourEvent.order)
            .all()
        )


def create_tour_for_admin(
        session: Session, name: str, start_date: datetime, end_date: datetime
):
    tour = Tour(
        id=uuid.uuid4(),
        name=name,
        start_date=start_date,
        end_date=end_date,
    )
    session.add(tour)
    session.commit()


# --- Login / logout ---
def show_login_form():
    st.title("Admin Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if not email or not password:
            st.warning("Please enter both email and password.")
            return
        result = firebase_login(email, password)
        if result is None:
            st.error("Invalid email or password.")
            return
        st.session_state["id_token"] = result["idToken"]
        st.session_state["user_email"] = email
        st.rerun()


def logout():
    if st.button("Logout"):
        st.session_state["id_token"] = None
        st.session_state["user_email"] = None
        st.session_state["selected_tour_id"] = None
        st.rerun()


# --- Session state init ---
if "id_token" not in st.session_state:
    st.session_state["id_token"] = None
if "user_email" not in st.session_state:
    st.session_state["user_email"] = None
if "selected_tour_id" not in st.session_state:
    st.session_state["selected_tour_id"] = None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if st.session_state["id_token"] is None:
    show_login_form()
else:
    user_info = verify_firebase_token(st.session_state["id_token"])

    if user_info is None:
        st.error("Session expired. Please log in again.")
        st.session_state["id_token"] = None
        st.session_state["user_email"] = None
        st.rerun()

    user_email = st.session_state["user_email"]

    if user_email != ADMIN_EMAIL:
        st.error("You do not have admin access.")
        logout()
    else:
        logout()
        st.write(f"Welcome *{user_email}*")

        all_tours = get_all_tours()

        # ---------------------------------------------------------------
        # Tour selector
        # ---------------------------------------------------------------
        st.title("Tour Management")

        if not all_tours:
            st.info("No tours exist yet. Create one below to get started.")
            selected_tour = None
        else:
            tour_options = {str(t.id): t.name for t in all_tours}

            # Default to the most recent tour if nothing is selected yet
            if st.session_state["selected_tour_id"] not in tour_options:
                st.session_state["selected_tour_id"] = list(tour_options.keys())[0]

            selected_tour_id = st.selectbox(
                "Select Tour to Manage",
                options=list(tour_options.keys()),
                format_func=lambda x: tour_options[x],
                index=list(tour_options.keys()).index(st.session_state["selected_tour_id"]),
                key="tour_selector",
            )

            # Persist the selection across reruns
            if selected_tour_id != st.session_state["selected_tour_id"]:
                st.session_state["selected_tour_id"] = selected_tour_id
                st.rerun()

            selected_tour = next(t for t in all_tours if str(t.id) == selected_tour_id)

        # ---------------------------------------------------------------
        # Tournament management — only shown when a tour is selected
        # ---------------------------------------------------------------
        if selected_tour:
            tour_id = str(selected_tour.id)
            events = get_all_tour_events(tour_id)
            max_order = max((e.order for e in events), default=0) + 1

            st.divider()
            st.title(f"Managing: {selected_tour.name}")

            # --- Add tournament ---
            st.header("Add a Tournament")
            tournament_name = st.text_input("Tournament Name")
            url = st.text_input("Tournament URL")
            points = st.number_input("Points", min_value=0)
            major = st.checkbox("Is this a major tournament?")
            tournament_order = st.number_input("Tournament order", value=max_order)

            if st.button("Submit tournament"):
                if tournament_name and url:
                    with SessionFactory() as session:
                        add_tournament_and_players(
                            session, tournament_name, url, int(points),
                            major, int(tournament_order), tour_id,
                        )
                    st.success(f"Tournament '{tournament_name}' added.")
                    st.rerun()
                else:
                    st.warning("Please fill in name and URL.")

            st.divider()

            # --- Remove tournament ---
            st.header("Remove a Tournament")
            if not events:
                st.info("No tournaments in this tour yet.")
            else:
                event_options = {str(e.id): e.name for e in events}
                remove_id = st.selectbox(
                    "Select tournament to remove",
                    options=list(event_options.keys()),
                    format_func=lambda x: event_options[x],
                )
                if st.button("Remove tournament"):
                    with SessionFactory() as session:
                        remove_tournament_and_player_points(session, remove_id)
                    st.success("Tournament removed.")
                    st.rerun()

            st.divider()

            # --- Rearrange tournaments ---
            st.header("Rearrange Tournaments")
            if not events:
                st.info("No tournaments to rearrange yet.")
            else:
                name_to_id = {e.name: str(e.id) for e in events}
                sorted_result = sort_items(list(name_to_id.keys()))

                if st.button("Save order"):
                    sorted_ids = [name_to_id[name] for name in sorted_result]
                    with SessionFactory() as session:
                        rearrange_tournament_order(session, sorted_ids)
                    st.success("Order updated.")
                    st.rerun()

        # ---------------------------------------------------------------
        # Create a New Tour — always visible at the bottom
        # ---------------------------------------------------------------
        st.divider()
        st.title("Create a New Tour")

        tour_name = st.text_input("Tour Name")
        tour_start_date = st.date_input("Start Date", key="tour_start")
        tour_end_date = st.date_input("End Date", key="tour_end")

        if st.button("Create Tour"):
            if tour_name and tour_start_date and tour_end_date:
                if tour_end_date < tour_start_date:
                    st.warning("End date must be after start date.")
                else:
                    with SessionFactory() as session:
                        create_tour_for_admin(
                            session, tour_name, tour_start_date, tour_end_date
                        )
                    st.success(f"Tour '{tour_name}' created.")
                    st.rerun()
            else:
                st.warning("Please fill in all fields.")
