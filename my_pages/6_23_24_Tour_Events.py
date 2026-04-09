import streamlit as st

import json

from google.cloud import firestore
from google.oauth2 import service_account


key_dict = json.loads(st.secrets["textkey2"])
creds = service_account.Credentials.from_service_account_info(key_dict)
db = firestore.Client(credentials=creds)

def showTournaments():

#leave as 2023
    posts_ref = db.collection("tournaments").order_by("order")
    
    for doc in posts_ref.stream():
        post = doc.to_dict()
        name = post["name"]
        url = post["url"]
        points = post["points"]
        major = post["major"]

        st.subheader(f"{name.replace('_', ' ')}")
        st.write(f":link: [{url}]({url})")
        st.write(f"Points: {points}")
        if major:
            st.write(f"Major")

    #export_players_to_csv()


showTournaments()
