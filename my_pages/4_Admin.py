import json
import httpx
import streamlit as st
import pandas as pd
from google.cloud import firestore
from google.oauth2 import service_account
from streamlit_sortables import sort_items
from admin_tasks import (
    add_tournament_and_players,
    rearrange_tournament_order,
    remove_tournament_and_player_points,
)
from pdga_scraper import get_all_tournaments

# --- Firebase setup ---
key_dict = json.loads(st.secrets["textkey2"])
creds = service_account.Credentials.from_service_account_info(key_dict)
db = firestore.Client(credentials=creds)

FIREBASE_WEB_API_KEY = st.secrets["firebase_web_api_key"]
ADMIN_EMAIL = st.secrets["admin_email"]  # e.g. "admin@yourdomain.com"


def firebase_login(email: str, password: str) -> dict | None:
    """Exchange email/password for a Firebase ID token."""
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
    """Verify an ID token and return the decoded user info."""
    url = (
        f"https://identitytoolkit.googleapis.com/v1/accounts:lookup"
        f"?key={FIREBASE_WEB_API_KEY}"
    )
    response = httpx.post(url, json={"idToken": id_token})
    if response.status_code != 200:
        return None
    users = response.json().get("users", [])
    return users[0] if users else None


# --- Session state init ---
if "id_token" not in st.session_state:
    st.session_state["id_token"] = None
if "user_email" not in st.session_state:
    st.session_state["user_email"] = None


# --- Login form ---
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


# --- Logout ---
def logout():
    if st.button("Logout"):
        st.session_state["id_token"] = None
        st.session_state["user_email"] = None
        st.rerun()


# --- Main app logic ---
if st.session_state["id_token"] is None:
    show_login_form()
else:
    # Verify token is still valid
    user_info = verify_firebase_token(st.session_state["id_token"])

    if user_info is None:
        st.error("Session expired. Please log in again.")
        st.session_state["id_token"] = None
        st.session_state["user_email"] = None
        st.rerun()

    user_email = st.session_state["user_email"]

    if user_email == ADMIN_EMAIL:
        logout()

        tournaments = get_all_tournaments(db)
        tournaments_list = list(map(lambda x: x.to_dict(), tournaments))
        tournament_df = pd.DataFrame(tournaments_list)
        max_value = 1

        if len(tournaments_list) > 0:
            default_order = tournament_df.sort_values(by="order")
            max_value = default_order["order"].max() + 1

        st.write(f"Welcome *{user_email}*")
        st.title("Add a Tournament")

        tournament_name = st.text_input("Tournament Name")
        url = st.text_input("Tournament Url")
        points = st.number_input("Points")
        major = st.checkbox("Is this a major tournament?")
        tournament_order = st.number_input("Tournament order", value=max_value)

        submit = st.button("Submit tournament")

        st.divider()

        st.title("Remove a tournament")
        tournaments = get_all_tournaments(db)
        names = [t.id for t in tournaments]

        remove_tournament = st.selectbox("Select which tournament to remove", names)
        remove = st.button("Remove tournament")

        st.divider()
        st.title("Rearrange Tournaments")

        tournament_sorter = get_all_tournaments(db)
        names_in_order = [t.id for t in tournament_sorter]
        sorted_items = sort_items(names_in_order)
        rearrange_tournaments = st.button("Rearrange tournaments")

        if remove_tournament and remove:
            remove_tournament_and_player_points(db, remove_tournament)

        if tournament_name and url and points and submit:
            add_tournament_and_players(
                db, tournament_name, url, points, major, tournament_order
            )

        if rearrange_tournaments and sorted_items:
            rearrange_tournament_order(db, sorted_items)

    else:
        st.error("You do not have admin access.")
        logout()