"""
Downloads the race results after f1.zip ends (2025 onwards) from the public Jolpica-F1 API, the community
continuation of the Ergast database the project's data comes from, and converts them to the project's
conventions so the forecast can start from the latest completed race.

Conventions (learned from the 1994-2024 feature store, see the asserts below):
  grid 0 (pit lane) or > 20  -> 20        finish = positionOrder, target_finish_position = min(finish, 20)
  retirement = any status other than Finished / Lapped / "+N Laps" (DNS and disqualified count as retirements)
  win = finish 1, podium = finish <= 3     IDs reuse the warehouse's driver / constructor / circuit refs

Usage: .venv/bin/python data/external/fetch_recent_results.py   (writes results_2025_onwards.csv, calendar_upcoming.csv)
"""

import json
import os
import sqlite3
import time
import urllib.request
from datetime import date

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
API = "https://api.jolpi.ca/ergast/f1"
HEADERS = {"User-Agent": "f1-race-intelligence-student-project"}


def get(path):
    for attempt in range(4):  # the API allows a few requests per second; back off on errors
        try:
            with urllib.request.urlopen(urllib.request.Request(f"{API}/{path}", headers=HEADERS), timeout=30) as r:
                return json.load(r)["MRData"]
        except Exception as e:
            err = e
            time.sleep(2 + 3 * attempt)
    raise err


def season_results(season):
    races, offset = {}, 0
    while True:
        page = get(f"{season}/results.json?limit=100&offset={offset}")
        for r in page["RaceTable"]["Races"]:  # one race can be split across pages
            races.setdefault(r["round"], {**r, "Results": []})["Results"] += r["Results"]
        offset += 100
        time.sleep(0.4)
        if offset >= int(page["total"]):
            return list(races.values())


def finished(status):
    return status in ("Finished", "Lapped") or status.startswith("+")


def build(first_season=2025):
    with sqlite3.connect(os.path.join(ROOT, "f1_warehouse.db")) as db:
        ref = {kind: dict(db.execute(sql).fetchall()) for kind, sql in [
            ("driver", "SELECT driver_ref, driver_id FROM DIM_DRIVER"),
            ("constructor", "SELECT constructor_ref, constructor_id FROM DIM_CONSTRUCTOR"),
            ("circuit", "SELECT circuit_name, circuit_id FROM DIM_CIRCUIT_SNOWFLAKE")]}  # warehouse circuit refs are placeholders
    store = pd.read_csv(os.path.join(ROOT, "data", "processed", "F1_RACE_LAB_FEATURES_1994_2024.csv"), usecols=["circuit_id", "circuit_name"])
    ref["circuit"].update(dict(zip(store["circuit_name"], store["circuit_id"])))
    ref["circuit"]["Lusail International Circuit"] = ref["circuit"]["Losail International Circuit"]  # same track, new spelling
    new_ids = {k: 9000 + len(v) for k, v in ref.items()}

    def project_id(kind, key):  # new drivers, teams and circuits after 2024 get IDs from 9000 up
        if key not in ref[kind]:
            new_ids[kind] += 1
            ref[kind][key] = new_ids[kind]
        return ref[kind][key]

    rows, dob, season = [], {}, first_season
    while True:
        races = season_results(season)
        if not races:
            break
        for d in get(f"{season}/drivers.json?limit=100")["DriverTable"]["Drivers"]:
            dob[d["driverId"]] = d.get("dateOfBirth")
        for r in sorted(races, key=lambda r: int(r["round"])):
            for x in r["Results"]:
                finish, grid = int(x["position"]), int(x["grid"])
                rows.append({
                    "race_id": 9000 + season % 100 * 100 + int(r["round"]), "season": season, "round": int(r["round"]),
                    "circuit_id": project_id("circuit", r["Circuit"]["circuitName"]), "circuit_name": r["Circuit"]["circuitName"],
                    "race_name": r["raceName"], "race_date": r["date"],
                    "driver_id": project_id("driver", x["Driver"]["driverId"]),
                    "driver_name": f'{x["Driver"]["givenName"]} {x["Driver"]["familyName"]}',
                    "driver_dob": dob.get(x["Driver"]["driverId"]),
                    "constructor_id": project_id("constructor", x["Constructor"]["constructorId"]),
                    "constructor_name": x["Constructor"]["name"],
                    "grid_position": 20 if grid == 0 or grid > 20 else grid,
                    "finish_position": finish, "target_finish_position": min(finish, 20),
                    "target_is_win": int(finish == 1), "target_is_podium": int(min(finish, 20) <= 3),
                    "target_is_dnf": int(not finished(x["status"])), "race_points": float(x["points"]),
                    "status": x["status"]})
        season += 1
        time.sleep(0.4)
    df = pd.DataFrame(rows)
    assert df.groupby("race_id")["target_is_win"].sum().eq(1).all(), "every race needs exactly one winner"
    assert df["grid_position"].between(1, 20).all()

    # the next races still to run: rest of the current season (and next season once its calendar is published)
    today, upcoming = date.today().isoformat(), []
    for s in (season - 1, season):
        for r in get(f"{s}.json?limit=40")["RaceTable"]["Races"]:
            if r["date"] > df["race_date"].max():
                upcoming.append({"season": s, "round": int(r["round"]), "race_name": r["raceName"], "race_date": r["date"],
                                 "circuit_id": project_id("circuit", r["Circuit"]["circuitName"]),
                                 "circuit_name": r["Circuit"]["circuitName"]})
    cal = pd.DataFrame(upcoming)
    df.to_csv(os.path.join(HERE, "results_2025_onwards.csv"), index=False)
    cal.to_csv(os.path.join(HERE, "calendar_upcoming.csv"), index=False)
    return df, cal, today


if __name__ == "__main__":
    df, cal, today = build()
    last = df.sort_values("race_date").iloc[-1]
    print(f"[+] {df['race_id'].nunique()} races, {len(df)} results, {df['season'].min()}-{df['season'].max()}; "
          f"latest: {last['season']} {last['race_name']} ({last['race_date']})")
    print(f"[+] upcoming after {today}:", ", ".join(f"{r.season} {r.race_name} ({r.race_date})" for r in cal.itertuples()))
