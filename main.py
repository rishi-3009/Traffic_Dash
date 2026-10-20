# main.py
# This file starts the game, runs the game loop, and draws every screen.
# The screen we are on is stored in app["state"]: "menu", "play", "report" or "leaderboard".
# Run this file with:  python main.py

import os                        # os builds the paths to the asset images
import pygame                    # pygame opens the window, draws shapes, reads keys and plays the clock
import data                      # loads and cleans the CSV files
import game                      # the rules: spawning, moving, hits, power-ups
import report                    # saves rides and works out the Run Report
from settings import SCREEN, SCREEN_W, SCREEN_H, FPS, LANES, PLAYER_Y, BASE_SPEED
from settings import SLOW_FACTOR, FLASH_MS, ROAD_COLOUR, LANE_MARK_COLOUR, HUD_COLOUR
from settings import TEXT_COLOUR, RED, GREEN, ORANGE


def load_image(filename, size):
    # Load one picture and shrink it to fit inside the size we need, without stretching it.
    # It is centred on a see-through box of exactly that size.
    # If the file is missing (or cannot be read) we return None, and the game draws a box instead
    path = os.path.join("assets", filename)
    if not os.path.exists(path):
        return None
    try:
        image = pygame.image.load(path).convert_alpha()
    except pygame.error:
        return None
    width, height = image.get_size()
    scale = min(size[0] / width, size[1] / height)
    fitted = pygame.transform.smoothscale(image, (int(width * scale), int(height * scale)))
    box = pygame.Surface(size, pygame.SRCALPHA)
    box.blit(fitted, ((size[0] - fitted.get_width()) // 2, (size[1] - fitted.get_height()) // 2))
    return box


def load_images(items):
    # Load every picture once, before the game loop starts. The dictionary key is the file name
    images = {}
    for it in items:
        images[it["image"]] = load_image(it["image"], (60, 60))
    images["scooter.png"] = load_image("scooter.png", (50, 80))
    images["road.png"] = load_image("road.png", SCREEN)
    return images


def load_fonts():
    # Pygame's built-in font is always available, so we use it with different sizes
    return {"big": pygame.font.Font(None, 56), "mid": pygame.font.Font(None, 40),
            "small": pygame.font.Font(None, 30), "tiny": pygame.font.Font(None, 20)}


def draw_text(screen, font, text, colour, x, y):
    # Draw text with its top-left corner at (x, y)
    screen.blit(font.render(text, True, colour), (x, y))


def draw_text_right(screen, font, text, colour, right_x, y):
    # Draw text so that its right edge sits at right_x
    width = font.size(text)[0]
    draw_text(screen, font, text, colour, right_x - width, y)


def draw_centred(screen, font, text, colour, y):
    # Draw text in the middle of the screen, from left to right, at height y
    surface = font.render(text, True, colour)
    screen.blit(surface, surface.get_rect(center=(SCREEN_W // 2, y)))


def draw_placeholder(screen, font, label, colour, rect):
    # Used when a PNG is missing: a coloured rounded box with the object's name on it
    pygame.draw.rect(screen, colour, rect, border_radius=10)
    surface = font.render(label, True, TEXT_COLOUR)
    screen.blit(surface, surface.get_rect(center=rect.center))


def handle_key(app, event):
    # Send each key press to the function for the screen we are on
    if app["state"] == "menu":
        handle_menu_key(app, event)
    elif app["state"] == "play":
        handle_play_key(app, event.key)
    elif app["state"] == "report":
        handle_report_key(app, event.key)
    elif app["state"] == "leaderboard":
        if event.key == pygame.K_m:
            app["state"] = "menu"


def handle_menu_key(app, event):
    # Enter starts a ride
    if event.key == pygame.K_RETURN:
        start_ride(app)
    # Backspace removes the last letter of the name
    elif event.key == pygame.K_BACKSPACE:
        app["name"] = app["name"][:-1]
    # L opens the leaderboard, but only while the name box is empty.
    # Otherwise the L is typed into the name, because names can contain letters
    elif event.key == pygame.K_l and app["name"] == "":
        app["board"] = report.load_leaderboard()
        app["state"] = "leaderboard"
    # Any other letter, digit or space is added to the name (12 characters at most)
    elif len(app["name"]) < 12 and (event.unicode.isalnum() or event.unicode == " "):
        app["name"] += event.unicode


def start_ride(app):
    # Use the typed name, or "Rider" if the box was left empty
    name = app["name"].strip()
    if name == "":
        name = "Rider"

    # Build the player and the run, and remember the time so the first item spawns after a short wait
    app["ride"] = {"player": game.new_player(), "run": game.new_run(name, 0), "active": [],
                   "last_spawn": pygame.time.get_ticks(), "scroll": 0,
                   "zone_seen": "Sitabuldi", "flash_until": 0}
    app["state"] = "play"


def handle_play_key(app, key):
    # One key tap moves the scooter exactly one lane. It cannot go past the left or right edge
    player = app["ride"]["player"]
    if key == pygame.K_LEFT and player["lane"] > 0:
        player["lane"] -= 1
    elif key == pygame.K_RIGHT and player["lane"] < len(LANES) - 1:
        player["lane"] += 1


def handle_report_key(app, key):
    # R rides again with the same name, M goes back to the menu
    if key == pygame.K_r:
        start_ride(app)
    elif key == pygame.K_m:
        app["state"] = "menu"


def update_play(app, frame_ms):
    # Everything that changes during a ride, done once per frame
    ride = app["ride"]
    run = ride["run"]
    player = ride["player"]
    now = pygame.time.get_ticks()

    # Step 2: find the zone for our distance, and start the "Entering..." message when it changes
    zone = game.current_zone(app["zones"], run["distance"])
    run["zone"] = zone["zone"]
    if run["zone"] != ride["zone_seen"]:
        ride["zone_seen"] = run["zone"]
        ride["flash_until"] = now + FLASH_MS

    # Step 3: move forward. Distance grows faster in harder zones, and time counts in seconds
    run["distance"] += 0.25 * zone["speed_mult"]
    run["time"] += frame_ms / 1000.0
    ride["scroll"] = (ride["scroll"] + BASE_SPEED * zone["speed_mult"]) % 60

    # Step 4: spawn one new item when the gap for this zone has passed
    if now - ride["last_spawn"] > zone["spawn_gap_ms"]:
        choice = game.pick_item(app["items"], zone)
        ride["active"].append(game.spawn(choice, zone))
        ride["last_spawn"] = now

    # Step 5: while Diet Coke is active the traffic moves at half speed
    slow_factor = SLOW_FACTOR if now < player["slow_until"] else 1

    # Step 6: move the items, add the points for anything we dodged, then check for hits
    ride["active"], earned = game.move_items(ride["active"], slow_factor, run)
    run["dodge_points"] += earned
    ride["active"] = game.check_hits(player, ride["active"], run)

    # Step 7: the score is the distance plus the dodge points
    run["score"] = int(run["distance"]) + run["dodge_points"]

    # Step 8: no lives left means the ride is over
    if player["lives"] <= 0:
        end_ride(app)


def end_ride(app):
    # Save the run to the CSV files, work out the report, and show the report screen
    run = app["ride"]["run"]
    report.save_run(run)
    app["report"] = report.run_report(run, app["items"])
    app["state"] = "report"


def draw_road(screen, images, scroll):
    # The road is either the road.png picture or a plain grey fill
    road = images.get("road.png")
    if road is None:
        screen.fill(ROAD_COLOUR)
    else:
        screen.blit(road, (0, 0))

    # Lane lines sit halfway between each pair of lane centres
    # Each dash is 30 pixels long with a 30 pixel gap, so one dash repeats every 60 pixels
    for i in range(len(LANES) - 1):
        x = (LANES[i] + LANES[i + 1]) // 2
        y = int(scroll) - 60
        while y < SCREEN_H:
            pygame.draw.rect(screen, LANE_MARK_COLOUR, (x - 2, y, 4, 30))
            y += 60


def draw_item(screen, images, fonts, it):
    # Draw one obstacle or power-up: its picture, or a coloured box if the picture is missing
    rect = pygame.Rect(LANES[it["lane"]] - 30, int(it["y"]), 60, 60)
    image = images.get(it["image"])
    if image is None:
        colour = GREEN if it["kind"] == "powerup" else ORANGE
        draw_placeholder(screen, fonts["tiny"], it["name"], colour, rect)
    else:
        screen.blit(image, rect)


def draw_scooter(screen, images, fonts, player):
    # The scooter sits in the player's lane, at the bottom of the screen
    rect = pygame.Rect(LANES[player["lane"]] - 25, PLAYER_Y, 50, 80)
    image = images.get("scooter.png")
    if image is None:
        draw_placeholder(screen, fonts["tiny"], "scooter", RED, rect)
    else:
        screen.blit(image, rect)

    # The helmet shield is shown as a green ring around the scooter
    if player["shield"]:
        pygame.draw.rect(screen, GREEN, rect.inflate(16, 16), width=3, border_radius=12)


def draw_hud(screen, fonts, ride, now):
    # The HUD is the bar across the top with the score, lives, distance, zone and status
    run = ride["run"]
    player = ride["player"]
    pygame.draw.rect(screen, HUD_COLOUR, (0, 0, SCREEN_W, 60))

    # Top line: score on the left, hearts for lives in the middle, distance in km on the right
    draw_text(screen, fonts["small"], "Score {}".format(run["score"]), TEXT_COLOUR, 10, 8)
    for i in range(max(player["lives"], 0)):
        pygame.draw.circle(screen, RED, (150 + i * 22, 22), 8)
    draw_text_right(screen, fonts["small"], "{:.1f} km".format(run["distance"] / 1000),
                    TEXT_COLOUR, SCREEN_W - 10, 8)

    # Bottom line: zone name on the left, and the power-up status on the right
    draw_text(screen, fonts["small"], run["zone"], TEXT_COLOUR, 10, 34)
    status = []
    if player["shield"]:
        status.append("Helmet ON")
    if now < player["slow_until"]:
        status.append("Diet Coke: slow traffic")
    draw_text_right(screen, fonts["small"], "  ".join(status), GREEN, SCREEN_W - 10, 34)


def draw_play(screen, fonts, images, app):
    # Draw the road, the items, the scooter and the HUD, in that order, so the scooter is on top
    ride = app["ride"]
    now = pygame.time.get_ticks()
    draw_road(screen, images, ride["scroll"])
    for it in ride["active"]:
        draw_item(screen, images, fonts, it)
    draw_scooter(screen, images, fonts, ride["player"])
    draw_hud(screen, fonts, ride, now)

    # The "Entering ..." message is shown for a short time after the zone changes
    if now < ride["flash_until"]:
        draw_centred(screen, fonts["big"], "Entering {}!".format(ride["run"]["zone"]), ORANGE, 300)


def draw_menu(screen, fonts, app):
    # Title, name box, and the controls
    screen.fill(ROAD_COLOUR)
    draw_centred(screen, fonts["big"], "Nagpur Traffic Dash", ORANGE, 120)
    draw_centred(screen, fonts["small"], "Type your name:", TEXT_COLOUR, 230)
    pygame.draw.rect(screen, HUD_COLOUR, (100, 260, 300, 50), border_radius=8)
    draw_centred(screen, fonts["mid"], app["name"], TEXT_COLOUR, 285)

    controls = ["Left / Right arrows = change lane", "Enter = ride",
                "L = leaderboard (name box must be empty)", "Backspace = delete a letter"]
    y = 400
    for line in controls:
        draw_centred(screen, fonts["small"], line, TEXT_COLOUR, y)
        y += 40


def report_rows(rep):
    # Turn the report dictionary into (label, value) pairs of text, ready to draw
    improvement = "Need 10 runs"
    if rep["improvement"] is not None:
        improvement = "{:+.1f}".format(rep["improvement"])
    return [("Games played", "{}".format(rep["games"])),
            ("Best score", "{}".format(rep["best"])),
            ("Average score", "{:.1f}".format(rep["average"])),
            ("Median score", "{:.1f}".format(rep["median"])),
            ("Consistency (std)", "{:.1f}".format(rep["consistency"])),
            ("Better than", "{}% of runs".format(rep["better_than"])),
            ("Top 10% score", "{:.1f}".format(rep["top10_score"])),
            ("Improvement", improvement),
            ("Obstacle types dodged", "{}".format(rep["types_dodged"]))]


def draw_wrapped(screen, font, text, colour, x, y, max_width):
    # Draw text on several lines so that no line is wider than max_width.
    # Returns the height where the next line of text should start
    line = ""
    for word in text.split(" "):
        test = word if line == "" else line + " " + word
        if font.size(test)[0] > max_width and line != "":
            draw_text(screen, font, line, colour, x, y)
            y += 30
            line = word
        else:
            line = test
    draw_text(screen, font, line, colour, x, y)
    return y + 30


def draw_crash_bars(screen, fonts, top_crashes, y):
    # A bar chart of the top 3 crash obstacles. The longest bar is 130 pixels, the rest are scaled to it
    draw_text(screen, fonts["small"], "Top crash obstacles", TEXT_COLOUR, 40, y)
    y += 35
    if not top_crashes:
        draw_text(screen, fonts["small"], "No crashes yet", TEXT_COLOUR, 40, y)
        return

    # The list is already sorted with the biggest count first
    biggest = top_crashes[0][1]
    for name, count in top_crashes:
        bar_width = int(count / biggest * 130)
        draw_text(screen, fonts["small"], name, TEXT_COLOUR, 40, y)
        pygame.draw.rect(screen, ORANGE, (200, y + 4, bar_width, 16))
        draw_text(screen, fonts["small"], "{}".format(count), TEXT_COLOUR, 200 + bar_width + 8, y)
        y += 40


def draw_report(screen, fonts, app):
    # The Run Report: this ride's result, the statistics, the never-dodged list and the crash chart
    screen.fill(ROAD_COLOUR)
    run = app["ride"]["run"]
    rep = app["report"]
    draw_centred(screen, fonts["big"], "Run Report", ORANGE, 50)
    draw_centred(screen, fonts["small"], "{} scored {} in {}".format(run["player"], run["score"],
                                                                     run["zone"]), TEXT_COLOUR, 95)

    # One row of text for each statistic. Values start at x = 290 so the labels never overlap them
    y = 135
    for label, value in report_rows(rep):
        draw_text(screen, fonts["small"], label, TEXT_COLOUR, 40, y)
        draw_text(screen, fonts["small"], value, ORANGE, 290, y)
        y += 30

    # The never-dodged list can be long, so it is wrapped onto more than one line
    never = ", ".join(sorted(rep["never_dodged"])) or "None"
    y = draw_wrapped(screen, fonts["small"], "Never dodged: " + never, ORANGE, 40, y + 10, 420)

    draw_crash_bars(screen, fonts, rep["top_crashes"], y + 30)
    draw_centred(screen, fonts["small"], "R = ride again      M = menu", TEXT_COLOUR, 700)


def draw_leaderboard(screen, fonts, app):
    # The top 5 runs, with the player, score and zone reached
    screen.fill(ROAD_COLOUR)
    draw_centred(screen, fonts["big"], "Leaderboard", ORANGE, 60)
    draw_text(screen, fonts["small"], "Player", TEXT_COLOUR, 40, 120)
    draw_text(screen, fonts["small"], "Score", TEXT_COLOUR, 230, 120)
    draw_text(screen, fonts["small"], "Zone reached", TEXT_COLOUR, 330, 120)

    if not app["board"]:
        draw_centred(screen, fonts["small"], "No runs yet. Go and play one!", TEXT_COLOUR, 300)

    y = 160
    for row in app["board"]:
        draw_text(screen, fonts["small"], "{}".format(row["player"]), TEXT_COLOUR, 40, y)
        draw_text(screen, fonts["small"], "{}".format(row["score"]), TEXT_COLOUR, 230, y)
        draw_text(screen, fonts["small"], "{}".format(row["zone_reached"]), TEXT_COLOUR, 330, y)
        y += 40
    draw_centred(screen, fonts["small"], "M = menu", TEXT_COLOUR, 700)


def draw_screen(screen, fonts, images, app):
    # Pick the right drawing function for the screen we are on
    if app["state"] == "menu":
        draw_menu(screen, fonts, app)
    elif app["state"] == "play":
        draw_play(screen, fonts, images, app)
    elif app["state"] == "report":
        draw_report(screen, fonts, app)
    elif app["state"] == "leaderboard":
        draw_leaderboard(screen, fonts, app)


def main():
    # Step 1: start pygame, open the window and make a clock to control the speed
    pygame.init()
    screen = pygame.display.set_mode(SCREEN)
    pygame.display.set_caption("Nagpur Traffic Dash")
    clock = pygame.time.Clock()

    # Step 2: load the data, pictures and fonts ONCE, before the game loop starts
    items, zones = data.load_all()
    images = load_images(items)
    fonts = load_fonts()

    # app is one dictionary that holds everything the screens need
    app = {"state": "menu", "name": "", "ride": None, "report": None, "board": [],
           "items": items, "zones": zones}
    frame_ms = 0
    running = True

    # The game loop: events, update, draw, show the picture, wait for the next frame
    while running:
        # 1. EVENTS: read every key press and check if the window was closed
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                handle_key(app, event)

        # 2. UPDATE: only the play screen changes over time
        if app["state"] == "play":
            update_play(app, frame_ms)

        # 3. DRAW: draw the current screen
        draw_screen(screen, fonts, images, app)
        pygame.display.flip()
        frame_ms = clock.tick(FPS)

    pygame.quit()


# Only start the game when this file is run directly with "python main.py"
if __name__ == "__main__":
    main()
