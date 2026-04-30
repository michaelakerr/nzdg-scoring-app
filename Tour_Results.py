import streamlit as st

pages = {
    "Current Tour Year (25/26)": [
        st.Page("my_pages/1_Tour_Results.py", title="Tour Results"),
        st.Page("my_pages/2_Tour_Events.py", title="Tour Events"),
    ],
    "Previous Tour Years": [
        # another nested breakpoint
        st.Page("my_pages/5_23_24_Tour_Results.py", title="Tour Results 23/24"),
        st.Page("my_pages/6_23_24_Tour_Events.py", title="Tour Events 23/24"),
        st.Page("my_pages/7_24_25_Tour_Results.py", title="Tour Results 24/25"),
        st.Page("my_pages/8_24_25_Tour_Events.py", title="Tour Events 24/25"),
    ],
    "More Information": [
        st.Page("my_pages/3_About_the_tour_points.py", title="About the Tour Points"),
    ],
    "Admin": [
        st.Page("my_pages/4_Admin.py", title="Admin"),
    ],
}

st.set_page_config(layout="wide")
st.logo("nzdg_logo.png")

pg = st.navigation(pages)
pg.run()
