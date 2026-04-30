import uuid
from io import StringIO

import pandas as pd
import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import joinedload


from models.models import User, RoundRating, TourResult, PointsLedger

TIER_BONUS_MULTIPLIER = 1
DECAY = 0.9

"""
Parse the tournament details from the PDGA website and return a dataframe with the player details WITHOUT their points for the tournament.
"""



def parse_pdga_site(url: str):
    # this will return a df with the tournament details from the url
    response = requests.get(url)

    soup = BeautifulSoup(response.text, "html.parser")
    divisions = soup.find_all("h3", {"class": "division"})

    # all divs
    list_of_divs = []

    for row in divisions:
        list_of_divs.append(row.get_text().split(" · ")[0])

    # Get players
    page = soup.find_all("details")
    players = pd.read_html(StringIO(str(page)))

    # Add division to each player df
    for index, div in enumerate(players):
        div["Div"] = list_of_divs[index]

    df = pd.concat(players)

    df.to_csv("raw.csv")
    # Clean the data

    df = df[df.Total != "DNF"]

    unnamed_map = {}

    for col in df.columns:
        if col.startswith("Unnamed"):
            col_idx = df.columns.get_loc(col)
            prev_col = df.columns[col_idx - 1]
            # get last number from prev_col which is like Rd1, Rd2 etc and create a new column name like rd1_rating, rd2_rating etc. This will be used to store the round ratings in the db
            round_of_rating = prev_col[-1] if prev_col.startswith("Rd") else None
            if prev_col.startswith("Rd"):
                unnamed_map[col] = f"round_{round_of_rating}_rating"

    df = df.rename(columns=unnamed_map)

    # Drop round score columns and other unwanted columns dynamically
    round_cols = [col for col in df.columns if col.startswith("Rd")]
    df = df.drop(
        round_cols + ["Points", "Rating", "Total", "Prize (USD)"],
        axis=1,
        errors="ignore",
    )

    df["Par"] = pd.to_numeric(df["Par"], errors="coerce", downcast="integer").fillna(0)
    # Drop if DNF in par
    df = df.dropna(subset=["Par"])
    # Dont need to rank as not combining groups
    # df = df.groupby("Div", group_keys=False).apply(custom_rank)

    df = df.rename(columns={"PDGA#": "PDGA"})

    # ztodo - add points calculation here based on the number of players in the division and the rank of the player
    df.to_csv("tournament_results.csv", index=False)
    return df


"""
Custom rank function to assign points based on the par and place of the player. If two players have the same par and place then they will get the same points.
"""


def custom_rank(group):
    group = group.sort_values(by=["Par", "Place"]).reset_index(drop=True)

    # Add a 'rank' column - in the case of same par and place then assign same points.
    group["Rank"] = group.groupby(["Par", "Place"]).ngroup() + 1

    return group


def calculate_points(df: pd.DataFrame, BASE_POINTS: int, MAJOR: bool):
    df = df.reset_index(drop=True)  # ← fixes duplicate indices from pd.concat
    df["Points"] = float(0)
    MAJOR_MULTIPLIER = 1.5 if MAJOR else TIER_BONUS_MULTIPLIER

    for div, group in df.groupby("Div"):
        print(f"Calculating points for division {div} with {len(group)} players")
        division_size = len(group)
        bonus_pool_size = (division_size - 1) * MAJOR_MULTIPLIER

        for index, row in group.iterrows():
            rank = row["Place"]

            decay_factor = round(DECAY ** (rank - 1), 4)
            base_points = round(BASE_POINTS * decay_factor, 2)
            bonus_points = round(bonus_pool_size * decay_factor, 2)
            total_points = round(base_points + bonus_points, 2)

            df.loc[index, "Points"] = total_points

            print(f"Player {row['Name']} gets {total_points} points (base: {base_points}, bonus: {bonus_points})")

    print("Finished calculating points for all players")
    return df


def trigger_tournament_added(session, payload: dict):
    """
    Called when a tournament is added. Parses the PDGA site, creates/updates players,
    saves round ratings and tour results, then calculates and saves points ledger entries.
    Two loops are required — the first commits tour results so that the second loop can
    query them when calculating points (including major event logic).
    """
    event_id = payload["event_id"]
    name = payload["name"]
    url = payload["url"]
    points = payload["points"]
    major = payload["major"]
    order = payload["order"]
    tour_id = payload["tour_id"]

    df = parse_pdga_site(url)
    df = calculate_points(df, points, major)
    df.to_csv("tournament_results_with_points.csv", index=False)

    # --- Loop 1: Create/update players, round ratings, and tour results ---
    # Must commit before loop 2 so tour results are queryable with their relationships
    player_map = {}  # Cache {player_id: division} for use in loop 2
    tour_results_to_add = []

    for index, row in df.iterrows():
        player = create_or_update_player(session, row)
        df.at[index, 'player_id'] = str(player.id)
        player_map[player.id] = row["Div"]

        rounds = create_round_ratings(session, row, player, event_id, tour_id)
        tour_result = create_tour_result_for_player(player, event_id, tour_id, row, rounds)
        tour_results_to_add.append(tour_result)

    session.add_all(tour_results_to_add)
    session.commit()

    # --- Loop 2: Calculate points ledger entries ---
    # Tour results are now in the DB, so relationships (e.g. tour_events.major) are accessible
    ledger_entries_to_add = []

    for _, row in df.iterrows():
        player = session.query(User).filter_by(id=row["player_id"]).first()
        # If a player has no pdga, we should actually be adding a column in the previous step
        division = row["Div"]
        event_points = row["Points"]

        all_tour_results = (
            session.query(TourResult)
            .filter_by(player_id=player.id, tour_id=tour_id, division=division)
            .options(joinedload(TourResult.tour_events))
            .all()
        )

        points_ledger_entry = session.query(PointsLedger).filter_by(
            player_id=player.id,
            division=division,
            tour_id=tour_id,
        ).first()

        if points_ledger_entry is None:
            points_ledger_entry = PointsLedger(
                id=uuid.uuid4(),
                player_id=player.id,
                tour_id=tour_id,
                division=division,
                total_points=event_points,
                event_points={str(event_id): event_points},
                all_events_played_and_points={str(event_id): event_points},
            )
        else:
            points_ledger_entry = _update_points_ledger(
                points_ledger_entry, all_tour_results
            )

        ledger_entries_to_add.append(points_ledger_entry)

    session.add_all(ledger_entries_to_add)
    session.commit()
    print(f"Finished adding players to points ledger and tour results for tournament: {name}")


def _update_points_ledger(
        points_ledger_entry: PointsLedger,
        all_tour_results: list[TourResult],
) -> PointsLedger:
    """
    Recalculates total points for a player's ledger entry based on all their tour results.
    Rules: top 6 results count, with a max of 2 majors included.
    """
    sorted_results = sorted(all_tour_results, key=lambda r: r.points, reverse=True)

    top_6 = []
    major_count = 0
    for result in sorted_results:
        if len(top_6) == 6:
            break
        if result.tour_events.major:
            if major_count < 2:
                top_6.append(result)
                major_count += 1
        else:
            top_6.append(result)

    points_ledger_entry.total_points = sum(r.points for r in top_6)
    points_ledger_entry.event_points = {
        str(r.tour_event_id): r.points for r in top_6
    }
    points_ledger_entry.all_events_played_and_points = {
        str(r.tour_event_id): r.points for r in sorted_results
    }

    return points_ledger_entry
def create_tour_result_for_player(player, event_id, tour_id, row, ratings):
    tour_result = TourResult(
        id=uuid.uuid4(),
        player_id=player.id,
        tour_event_id=event_id,
        tour_id=tour_id,
        division=row["Div"],
        place = row["Place"],
        points=row["Points"],
    )
    tour_result.round_ratings = ratings
    return tour_result

def create_round_ratings(session, row, player, event_id, tour_id):
    rounds_to_add = []

    for col in row.index:
        # Round is like rd1_rating, rd2_rating etc. We want to extract the round name and the rating and save it to the db
        if col.startswith("round_") and col.endswith("_rating"):
            rating = row[col]
            round_of_rating = col.split("_")[1]  # Extract the round name from the column name
            if pd.notna(rating) and rating > 0:
                build_round = RoundRating(
                    id=uuid.uuid4(),
                    player_id=player.id,
                    tour_event_id=event_id,
                    tour_id=tour_id,
                    rating=rating,
                    round=round_of_rating,
                )
                rounds_to_add.append(build_round)
    return rounds_to_add


def create_or_update_player(session, row):

    # This function will create a new player in the db if they dont exist or update the existing player if they do exist
    # For simplicity we will just create a new player with the same name and assume they are the same player. In a real application we would need to have a more robust way of identifying players.
        player = session.query(User).filter_by(pdga_number=row["PDGA"]).first()

        if not player:
            pdga_number = row["PDGA"] if pd.notna(row["PDGA"]) else None
            player = User(
                id=uuid.uuid4(),
                given_name=row["Name"].split(" ")[0],
                last_name=row["Name"].split(" ")[-1],
                pdga_number=pdga_number,
                division=row["Div"]
            )
            session.add(player)
            session.commit()

        return player
