import pandas as pd
import streamlit as st


def show_worked_example():
    st.subheader("Worked Example")
    st.caption("21 players · Nationals · 70 base points · 1.5× multiplier")

    st.markdown("#### Step 1 — Competitive Field Points")
    st.markdown("""
    Competitive field points reward divisions with more players. They are calculated from the 
    number of players minus one, multiplied by the event multiplier.
    
    > **(Players − 1) × Multiplier = Competitive Field Points**  
    > (21 − 1) × 1.5 = **30 competitive field points**
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Base Points", "70")
    with col2:
        st.metric("Competitive Field Points", "30", help="(21-1) × 1.5")
    with col3:
        st.metric("Total Available (1st place)", "100")

    st.markdown("#### Step 2 — Points by Position (90% decay)")
    st.markdown("""
    First place earns the full 100 points. Every position below earns 90% of the position above it.
    Both base points and competitive field points decay at the same rate.
    """)

    places = [1, 2, 3, 4, 5, 10, 15, 20]
    rows = []
    for place in places:
        decay = 0.9 ** (place - 1)
        base = round(70 * decay, 2)
        field = round(30 * decay, 2)
        total = round(base + field, 2)
        suffix = "st" if place == 1 else "nd" if place == 2 else "rd" if place == 3 else "th"
        rows.append({
            "Place": f"{place}{suffix}",
            "Base Points": base,
            "Competitive Field Points": field,
            "Total Earned": total,
        })

    df = pd.DataFrame(rows)
    st.dataframe(
        df,
        hide_index=True,
        width="stretch",
        column_config={
            "Place": st.column_config.TextColumn("Place", width="small"),
            "Base Points": st.column_config.NumberColumn("Base Points", format="%.2f"),
            "Competitive Field Points": st.column_config.NumberColumn("Competitive Field Points", format="%.2f"),
            "Total Earned": st.column_config.NumberColumn("Total Earned", format="%.2f"),
        }
    )


def show_about():
    st.title("NZDG Tour Points System")
    st.markdown("Understanding how tour points are calculated and awarded across New Zealand disc golf events.")

    st.divider()

    # --- Overview ---
    st.header("Overview")
    st.markdown("""
    The NZDG Tour Points System is designed to be fair, flexible, and rewarding for all divisions,
    regardless of size or layout. Every division operates independently, giving Tournament Directors 
    full discretion over course layouts without impacting points equity.
    """)

    col1, col2 = st.columns(2)
    with col1:
        st.success("**Single player divisions** receive only the base points for the event.")
    with col2:
        st.success("**Multi-player divisions** earn base points **plus** competitive field points based on field size and placing.")

    st.divider()

    # --- Event Tiers ---
    st.header("Event Points & Multipliers")
    st.markdown("There are two event types, each with their own base points and multiplier:")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Majors")
        st.markdown("*Nationals & Island Championships*")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Base Points", "70 pts")
        with c2:
            st.metric("Multiplier", "1.5×")

    with col2:
        st.markdown("#### Standard Events")
        st.markdown("*All other sanctioned events*")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Base Points", "50 pts")
        with c2:
            st.metric("Multiplier", "1.0×")

    st.caption("Unsanctioned tournaments are not eligible for tour points.")

    st.divider()

    # --- How Points Work ---
    st.header("How Points Are Calculated")

    st.subheader("Step 1 — Competitive Field Points")
    st.markdown("""
    Every division earns competitive field points on top of the base points to reward larger, 
    more competitive fields. These points reflect the depth of competition in your division.

    > **Competitive Field Points = (Players − 1) × Event Multiplier**

    The *minus one* exists because a single-player division shouldn't earn any competitive field points.
    The **event multiplier** reflects the importance of the event — Nationals and Island Championships 
    carry a **1.5× multiplier**, while all other events use **1.0×**.
    """)

    st.subheader("Step 2 — Total Points on Offer")
    st.markdown("""
    Base points and competitive field points are added together. First place takes home the full total.

    > **Total Points = Base Points + Competitive Field Points**
    """)

    st.subheader("Step 3 — Points Decay by Position")
    st.markdown("""
    Every position below first earns **90% of what the position above it earns** — a geometric decay curve 
    that applies equally to both base points and competitive field points.

    > **Points for place N = Total Points × 0.9^(N−1)**

    Second place earns 90% of first, third earns 81%, and so on. Every placing earns meaningful 
    points, but finishing higher is always rewarded.
    """)

    st.divider()

    show_worked_example()

    st.divider()

    # --- Overall Tour Rankings ---
    st.header("Overall Tour Rankings")
    st.markdown("""
    A player's overall tour ranking is calculated from their **best 6 results** across all tour events, 
    with a maximum of **2 major events** counted toward the total.

    This rewards consistency across the season while ensuring that majors remain prestigious 
    without dominating the standings for players who only attend large events.
    """)

    col1, col2 = st.columns(2)
    with col1:
        st.success("Best **6** events count toward total")
    with col2:
        st.success("Maximum **2 majors** included")

    st.caption("Full policy: https://www.newzealanddiscgolf.org.nz/_files/ugd/acb9ce_836d0cb72ab845be9073b1987bc5f49c.pdf")

    st.divider()

    # --- Feedback ---
    st.header("Feedback")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Tour Feedback**  
        [Submit feedback via Google Form](https://docs.google.com/forms/d/e/1FAIpQLSdeMRWGHI0wabvJAr8fga5WQIZRrQbTPWxL28SYHHdbFtSlxg/viewform)
        """)
    with col2:
        st.markdown("""
        **Points System Queries**  
        Email Michaela Kerr: mikki.mjk@gmail.com
        """)


show_about()