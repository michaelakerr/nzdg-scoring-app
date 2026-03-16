from src.trigger.trigger_tournament_added import trigger_tournament_added

URL="https://www.pdga.com/tour/event/85604"
if __name__ == '__main__':
    payload = {
        "event_id": "fb8663f9-2534-405c-9814-2b3522c68866",
        "name": "Nationals 2025",
        "url": URL,
        "points": 70,
        "major": True,
        "order": 1,
        "tour_id": "206c92d5-62c9-4e27-9b8e-97c94f59e8ae"
    }
    trigger_tournament_added(payload)
    #parse_pdga_site(URL)
