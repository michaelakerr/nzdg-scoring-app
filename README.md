# NZDG Tour Points System

A Streamlit app that explains and demonstrates how tour points are calculated across New Zealand disc golf events.

## What the App Does

The app presents the NZDG tour points system in a structured, readable format. It walks through the scoring rules, shows how points are calculated step by step, and includes a worked example with a live table of points by finishing position.

## Scoring System

Points are made up of two components: **base points** and **competitive field points**.

### Event Types

| Event Type | Base Points | Multiplier |
|---|---|---|
| Majors (Nationals, Island Championships) | 70 pts | 1.5x |
| Standard sanctioned events | 50 pts | 1.0x |

Unsanctioned tournaments are not eligible for tour points.

### Calculation

1. **Competitive field points** reward larger divisions: `(Players - 1) x Multiplier`
2. **Total points on offer** for first place: `Base Points + Competitive Field Points`
3. **Points by position** decay at 90% per place: `Total Points x 0.9^(N-1)`

A single-player division receives only the base points, with no competitive field points.

### Overall Tour Rankings

A player's tour ranking is based on their best 6 results across the season, with a maximum of 2 major events counted. This rewards consistency while keeping majors meaningful without allowing them to dominate the standings.

## App Structure

The app is a single-page Streamlit view built from two functions:

- `show_about()` — renders the full explanation of the points system, including event tiers, calculation steps, ranking rules, and feedback links
- `show_worked_example()` — displays a concrete example (21 players, Nationals, 70 base points, 1.5x multiplier) with a table of points for selected finishing positions

## Running the App

```bash
python3 -m venv env
source env/bin/activate
pip install requirements.txt
streamlit run Tour_Results.py
```