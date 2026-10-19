# settings.py
# This file only holds constants (values that never change while the game runs).
# Other files import these names, for example: from settings import FPS

# Window size in pixels: width and height.
# We store width and height together in a tuple (a fixed group of values).
SCREEN_W, SCREEN_H = 500, 750
SCREEN = (SCREEN_W, SCREEN_H)    # tuple

# Frames per second: how many times the game screen is redrawn each second.
FPS = 60

# Centre x position (left to right) of each of the 4 lanes.
LANES = (110, 210, 310, 410)     # tuple: centre x of each lane

# The height (y position) where the top of the car sits.
PLAYER_Y = 640                   # top of the car

# Speed in pixels per frame, before the zone and item multipliers are applied.
BASE_SPEED = 5                   # pixels per frame before multipliers

# Lives: how many hits the player can take, and the most lives they can hold.
START_LIVES = 3
MAX_LIVES = 5

# Diet Coke power-up: how long it lasts (in milliseconds) and how much it slows traffic.
SLOW_MS = 4000                   # Diet Coke slows traffic for 4 seconds
SLOW_FACTOR = 0.5                # 0.5 means things move at half speed

# How long the "Entering Dharampeth!" message stays on screen, in milliseconds.
FLASH_MS = 2000

# Colours as RGB tuples (red, green, blue), each value from 0 to 255.
# road, lane marks, HUD, text, red, green, orange
ROAD_COLOUR = (60, 60, 66)
LANE_MARK_COLOUR = (240, 240, 240)
HUD_COLOUR = (25, 25, 35)
TEXT_COLOUR = (250, 250, 250)
RED = (220, 50, 50)
GREEN = (60, 200, 90)
ORANGE = (255, 150, 0)
