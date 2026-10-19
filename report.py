# report.py
# This file saves each ride to CSV files, works out the Run Report numbers,
# and reads the leaderboard.

import os                        # os checks whether files exist
import numpy as np               # numpy gives us the maths: max, mean, median, std, percentile
import pandas as pd              # pandas reads the CSV files as tables

RUNS_PATH = os.path.join("data", "runs.csv")
CRASHES_PATH = os.path.join("data", "crashes.csv")


def count_rows(path):
    # Count the data rows in a CSV file, not counting the header line
    # A missing file has 0 rows
    if not os.path.exists(path):
        return 0
    with open(path) as f:
        lines = f.readlines()
    return max(len(lines) - 1, 0)


def save_run(run):
    # The new run number is one more than the number of runs already saved
    run_id = count_rows(RUNS_PATH) + 1
    run["id"] = run_id

    # Check if the file exists BEFORE we open it, because opening in "a" mode creates it
    is_new = not os.path.exists(RUNS_PATH)

    # Commas separate the columns, so we remove any commas from the player's name
    clean_name = run["player"].replace(",", "")

    # Append (add to the end) one line for this run
    with open(RUNS_PATH, "a") as f:
        # Write the header line only when the file is brand new
        if is_new:
            f.write("run_id,player,date,distance_m,score,time_s,zone_reached,dodged,powerups,crashes\n")
        f.write("{},{},{},{},{},{},{},{},{},{}\n".format(
            run_id, clean_name, run["date"], round(run["distance"], 1), run["score"],
            round(run["time"], 1), run["zone"], run["dodged"], run["powerups"], len(run["crashes"])))

    # Each crash also gets its own line in the crashes file
    save_crashes(run_id, run["crashes"])


def save_crashes(run_id, crashes):
    # Same idea as save_run: check if the file is new before opening it
    is_new = not os.path.exists(CRASHES_PATH)
    with open(CRASHES_PATH, "a") as f:
        if is_new:
            f.write("run_id,obstacle,zone,second\n")
        # Loop over every crash this run and write one line for each
        for crash in crashes:
            f.write("{},{},{},{}\n".format(run_id, crash["obstacle"], crash["zone"], crash["second"]))


def run_report(run, items):
    # Read every saved score. save_run must be called first, so this run is in the file
    scores = np.array(pd.read_csv(RUNS_PATH)["score"])

    # A dictionary holds all the numbers we will draw on the report screen
    report = {}
    report["games"] = len(scores)
    report["best"] = scores.max()
    report["average"] = scores.mean()
    report["median"] = np.median(scores)
    report["consistency"] = scores.std()

    # How many percent of past runs this run beat
    report["better_than"] = int(round((scores < run["score"]).mean() * 100))

    # The score that 90% of runs are below
    report["top10_score"] = np.percentile(scores, 90)

    # Improvement only means something after 10 or more runs. Otherwise it stays None
    report["improvement"] = None
    if len(scores) >= 10:
        report["improvement"] = scores[-5:].mean() - scores[:5].mean()

    # Dodging stats: how many kinds of obstacle this run dodged, and which ones it never dodged
    report["types_dodged"] = len(run["types_dodged"])
    obstacle_names = set()
    for it in items:
        if it["kind"] == "obstacle":
            obstacle_names.add(it["name"])
    # Set difference: all obstacle names, minus the names this run dodged
    report["never_dodged"] = obstacle_names - run["types_dodged"]

    report["top_crashes"] = top_crashes()
    return report


def top_crashes():
    # No crashes file yet means nobody has crashed, so the list is empty
    if not os.path.exists(CRASHES_PATH):
        return []

    # Count the crashes for each obstacle, put the biggest first, and keep the top 3
    crashes = pd.read_csv(CRASHES_PATH)
    counts = crashes.groupby("obstacle").size().sort_values(ascending=False).head(3)

    # Return a list of (obstacle name, count) pairs
    return list(counts.items())


def load_leaderboard():
    # No runs saved yet means an empty leaderboard
    if not os.path.exists(RUNS_PATH):
        return []

    # Sort by score, highest first, and keep the top 5 rows
    table = pd.read_csv(RUNS_PATH)
    table = table.sort_values("score", ascending=False)
    return table.head(5).to_dict("records")
