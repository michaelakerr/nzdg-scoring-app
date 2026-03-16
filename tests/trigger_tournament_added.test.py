from src.trigger.trigger_tournament_added import trigger_tournament_added

URL="https://www.pdga.com/tour/event/85604"
if __name__ == '__main__':
    payload = {
        "event_id": 83980,
        "name": "Nationals 2025",
        "url": URL,
        "points": 70,
        "major": True,
        "order": 1,
        "tour_id": 1
    }
    trigger_tournament_added(payload)
    #parse_pdga_site(URL)
