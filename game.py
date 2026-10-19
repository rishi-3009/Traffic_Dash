# game.py
# This file holds the rules of the game: picking zones, spawning items, moving them,
# checking hits and applying power-ups.

import datetime                  # datetime gives us today's date for the run record
import numpy as np               # numpy gives us random choices and random numbers
import pygame                    # pygame gives us rectangles (Rect) for checking collisions
from settings import LANES, PLAYER_Y, BASE_SPEED, SCREEN_H, SLOW_MS, MAX_LIVES, START_LIVES


def new_player():
    # Build the player's dictionary when a ride starts
    # lane 1 is the second lane from the left (lanes count from 0)
    return {"lane": 1, "lives": START_LIVES, "shield": False, "slow_until": 0}


def new_run(player_name, run_id):
    # Build the record of one ride. It starts in the Sitabuldi zone.
    # types_dodged is a set, so each obstacle name is only stored once
    return {"id": run_id, "player": player_name, "date": datetime.date.today().isoformat(),
            "distance": 0.0, "dodge_points": 0, "score": 0, "time": 0.0, "zone": "Sitabuldi",
            "dodged": 0, "powerups": 0, "types_dodged": set(), "crashes": []}


def current_zone(zones, distance):
    # The zones are sorted by start_m, so we keep the last zone we have reached
    chosen = zones[0]
    for zone in zones:
        if zone["start_m"] <= distance:
            chosen = zone
    return chosen


def pick_item(items, zone):
    # Step 1: keep only the items this zone allows, using a plain for loop and "in"
    choices = []
    for item in items:
        if item["name"] in zone["allowed"]:
            choices.append(item)

    # Step 2: make a list of the spawn weights, one weight per choice
    weights = []
    for item in choices:
        weights.append(item["spawn_weight"])
    weights = np.array(weights)

    # Step 3: change the weights into probabilities that add up to 1
    # A bigger weight means that item is picked more often
    probs = weights / weights.sum()

    # Step 4: pick one position in the list using those probabilities, and return that item
    return choices[np.random.choice(len(choices), p=probs)]


def spawn(item, zone):
    # Pick a random lane: 0, 1, 2 or 3 (randint does not include the upper number)
    lane = int(np.random.randint(0, 4))

    # Make a new dictionary for this item on the road.
    # It starts just above the screen (y = -80) and its speed depends on the zone
    new_item = {"name": item["name"], "kind": item["kind"], "effect": item["effect"],
                "damage": int(item["damage"]), "points": int(item["points"]),
                "image": item["image"], "lane": lane, "y": -80.0,
                "speed": BASE_SPEED * item["speed"] * zone["speed_mult"]}
    return new_item


def move_items(active, slow_factor, run):
    # We build a NEW list for the items that are still on screen.
    # Removing items from a list while looping over it can skip the next item, so we avoid that.
    still_on_screen = []

    # Points earned by dodging this frame. The caller adds them to the run's total.
    dodge_points = 0
    for it in active:
        # Move the item down. slow_factor is 0.5 while chai is active, otherwise 1
        it["y"] += it["speed"] * slow_factor

        if it["y"] > SCREEN_H:
            # The item fell off the bottom. Only obstacles count as dodged, power-ups just vanish
            if it["kind"] == "obstacle":
                dodge_points += it["points"]
                run["dodged"] += 1
                run["types_dodged"].add(it["name"])
        else:
            still_on_screen.append(it)
    return still_on_screen, dodge_points


def check_hits(player, active, run):
    # The scooter's box: 50 pixels wide, 80 tall, in the player's lane at the bottom
    player_rect = pygame.Rect(LANES[player["lane"]] - 25, PLAYER_Y, 50, 80)

    # Keep only the items we did not touch. Touched items are handled and then left out.
    remaining = []
    for it in active:
        # The item's box. y is a decimal number, so we turn it into a whole number for Rect
        item_rect = pygame.Rect(LANES[it["lane"]] - 30, int(it["y"]), 60, 60)
        if player_rect.colliderect(item_rect):
            touch_item(player, it, run)
        else:
            remaining.append(it)
    return remaining


def touch_item(player, it, run):
    # Case 1: a power-up. Give the player its effect and count it
    if it["kind"] == "powerup":
        apply_powerup(player, it["effect"])
        run["powerups"] += 1

    # Case 2: an obstacle while the helmet shield is on. The shield breaks and there is no damage
    elif player["shield"]:
        player["shield"] = False

    # Case 3: an obstacle with no shield. Lose lives and write down the crash
    else:
        player["lives"] -= it["damage"]
        run["crashes"].append({"obstacle": it["name"], "zone": run["zone"],
                               "second": int(run["time"])})


def apply_powerup(player, effect):
    # pygame.time.get_ticks() gives the time in milliseconds since the game started
    now = pygame.time.get_ticks()

    # Helmet: turn the shield on
    if effect == "shield":
        player["shield"] = True

    # Chai: traffic slows down until the time in slow_until
    elif effect == "slow":
        player["slow_until"] = now + SLOW_MS

    # Petrol: one extra life, but never more than MAX_LIVES
    elif effect == "life":
        player["lives"] = min(player["lives"] + 1, MAX_LIVES)
