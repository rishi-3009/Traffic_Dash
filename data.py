# data.py
# This file loads the two CSV files and cleans the messy obstacle data.
# The CSV files themselves are never changed; we clean them in the computer's memory.

import os                        # os helps us build file paths and check if files exist
import numpy as np               # numpy gives us NaN (the "missing value" marker) and maths tools
import pandas as pd              # pandas reads and cleans tables of data


def load_obstacles(path=os.path.join("data", "obstacles_raw.csv")):
    # Step 1: stop early with a clear message if the file is missing
    if not os.path.exists(path):
        print("Could not find the obstacles file: {}".format(path))
        return None

    # Step 2: read the CSV file into a table (a DataFrame)
    df = pd.read_csv(path)

    # Step 3: "??" and "##" are typing mistakes, so we turn them into missing values (NaN)
    df = df.replace(["??", "##"], np.nan)

    # Step 4: remove extra spaces and make names lower case, so " Auto " becomes "auto"
    # The lambda is a tiny one-line function that does the clean-up for every row
    df["name"] = df["name"].apply(lambda x: x.strip().lower())
    df["kind"] = df["kind"].apply(lambda x: x.strip().lower())

    # Step 5: these columns must be numbers, so we convert them to float (decimal numbers)
    for column in ["speed", "damage", "points", "spawn_weight"]:
        df[column] = df[column].astype(float)

    # Step 6: show how many missing values each column has before we fill them
    print("Missing values before filling:")
    print(df.isnull().sum())

    # Step 7: fill the missing values
    # Speed uses the median, because the median is not pulled around by extreme values
    df["speed"] = df["speed"].fillna(df["speed"].median())
    # Damage uses the mode (most common value), because damage must be a whole number of lives
    df["damage"] = df["damage"].fillna(df["damage"].mode()[0])
    # Spawn weight uses the median, so one strange value cannot change the odds too much
    df["spawn_weight"] = df["spawn_weight"].fillna(df["spawn_weight"].median())

    # Step 8: remove repeated rows. The cow row appears twice in the raw file, we keep the first one
    df = df.drop_duplicates(subset=["name"], keep="first")

    # Step 9: save the cleaned table to a new file and give it back to the caller
    df.to_csv(os.path.join("data", "obstacles_clean.csv"), index=False)
    return df


def load_zones(path=os.path.join("data", "zones.csv")):
    # Stop early with a clear message if the zones file is missing
    if not os.path.exists(path):
        print("Could not find the zones file: {}".format(path))
        return None

    # Read the file, sort the zones by where they start on the road
    zones_table = pd.read_csv(path)
    zones_table = zones_table.sort_values("start_m")

    # Turn each row into a dictionary, so the game can read zone["speed_mult"] and so on
    zones = zones_table.to_dict("records")

    # The allowed column is one text value like "cow|auto|bus"
    # split("|") cuts it into a list of names: ["cow", "auto", "bus"]
    for z in zones:
        z["allowed"] = z["allowed"].split("|")
    return zones


def load_all():
    # Load both files and give back two lists: the items and the zones
    items_table = load_obstacles()
    zones = load_zones()

    # If a file was missing, use an empty list so the game does not crash
    items_list = []
    if items_table is not None:
        items_list = items_table.to_dict("records")
    if zones is None:
        zones = []
    return items_list, zones
