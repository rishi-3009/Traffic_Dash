# Nagpur Traffic Dash — Build Instructions for Claude Code

You are building **Nagpur Traffic Dash**, a lane-based endless-runner game in Pygame, for a 2nd-year B.Tech (CSE) Software Lab miniproject. Four beginner students must **explain every line in a viva**, so simplicity and clarity matter more than cleverness or performance.

Read this whole file before writing any code. Follow the design exactly. If something is ambiguous, choose the simplest option and leave a comment saying what you chose.

---

## 1. Hard rules for the code

1. **Libraries:** Python 3.10+, `pygame` (or `pygame-ce`), `pandas`, `numpy`, and the standard library (`os`, `datetime`). Nothing else.
2. **No classes.** Use only lists, dictionaries, tuples, sets and functions.
3. **Short functions.** Aim for under ~30 lines each, one clear job per function.
4. **Comment every block** in plain English that a beginner can read aloud in a viva.
5. Prefer `"{}".format(...)` for strings. Avoid f-strings, complex comprehensions, `lambda` beyond the cleaning step, decorators, generators, type hints, `*args`/`**kwargs`, and `global` where a return value works.
6. **No hard-coded game balance.** Obstacle behaviour and zone difficulty must come from the CSV files.
7. **Missing images must not crash the game.** If a PNG is missing, draw a coloured rounded rectangle with the object's name instead.
8. The game must run with `python main.py` on **Windows**. Use relative paths built with `os.path.join`.

The concepts the code must visibly use: variables/operators, if/elif/else, while/for loops, lists, tuples, strings (`split`, `strip`, `lower`, `format`), sets (including set difference), dictionaries (including a list of dictionaries inside a dictionary), functions with default arguments and multiple return values, lambda, file handling with append mode and `os.path.exists`, NumPy (weighted `random.choice`, `randint`, array maths, `max`/`mean`/`median`/`std`, boolean arrays, slicing, `percentile`), and Pandas (`read_csv`, `replace`, `apply`, `astype`, `isnull`, `fillna` with median and mode, `drop_duplicates`, `to_dict("records")`, `sort_values`, `groupby`, `idxmax`/`idxmin`, `describe`, `skew`, `corr`).

---

## 2. Folder structure

```
NagpurTrafficDash/
├── main.py            # starts the game, game loop, screens (state)
├── settings.py        # constants only
├── data.py            # load + clean obstacles_raw.csv, load zones.csv
├── game.py            # spawning, moving, collisions, power-ups, zones
├── report.py          # save to CSV, Run Report stats, leaderboard
├── analysis.ipynb     # analysis of play data
├── README.md          # how to install and run (Windows, beginner level)
├── data/
│   ├── obstacles_raw.csv
│   └── zones.csv      # runs.csv and crashes.csv are created by the game
└── assets/            # scooter.png, cow.png, auto.png, bus.png, pothole.png, rickshaw.png,
                       # dog.png, barricade.png, helmet.png, chai.png, petrol.png, road.png (all optional)
```

---

## 3. Input data files (create exactly these)

The mistakes in `obstacles_raw.csv` are **intentional**; they exist so the cleaning code has something to fix. Do not fix them in the CSV.

`data/obstacles_raw.csv`
```
name,kind,image,speed,damage,points,spawn_weight,effect
cow,obstacle,cow.png,0.6,1,15,25,none
 Auto ,obstacle,auto.png,1.3,1,10,30,none
bus,obstacle,bus.png,0.9,2,20,10,none
pothole,obstacle,pothole.png,1.0,1,5,25,none
cycle_rickshaw,obstacle,rickshaw.png,??,1,10,15,none
stray_dog,obstacle,dog.png,1.5,,15,15,none
barricade,obstacle,barricade.png,1.0,1,5,##,none
cow,obstacle,cow.png,0.6,1,15,25,none
helmet,powerup,helmet.png,1.0,0,0,6,shield
chai,powerup,chai.png,1.0,0,0,6,slow
petrol,powerup,petrol.png,1.0,0,0,4,life
```

`data/zones.csv`
```
zone,start_m,speed_mult,spawn_gap_ms,allowed
Sitabuldi,0,1.0,1100,cow|auto|cycle_rickshaw|pothole|helmet|chai
Dharampeth,800,1.25,950,cow|auto|stray_dog|pothole|bus|helmet|chai|petrol
Wardha Road,1800,1.55,800,auto|bus|barricade|pothole|stray_dog|helmet|petrol
Ring Road,3000,1.9,650,bus|auto|barricade|cow|pothole|chai|petrol
```

---

## 4. `settings.py`

```python
SCREEN_W, SCREEN_H = 500, 750
SCREEN = (SCREEN_W, SCREEN_H)    # tuple
FPS = 60
LANES = (110, 210, 310, 410)     # tuple: centre x of each lane
PLAYER_Y = 640                   # top of the scooter
BASE_SPEED = 5                   # pixels per frame before multipliers
START_LIVES = 3
MAX_LIVES = 5
SLOW_MS = 4000                   # chai lasts 4 seconds
SLOW_FACTOR = 0.5
# colours as RGB tuples: road, lane marks, HUD, text, red, green, orange
```

---

## 5. `data.py` — cleaning (must match exactly)

### `load_obstacles(path=os.path.join("data", "obstacles_raw.csv"))`
1. If the file does not exist (`os.path.exists`), print a clear message and return `None`.
2. `df = pd.read_csv(path)`
3. `df = df.replace(["??", "##"], np.nan)`
4. `df["name"] = df["name"].apply(lambda x: x.strip().lower())`, and the same for `kind`
5. Convert `speed, damage, points, spawn_weight` with `astype(float)`
6. `print(df.isnull().sum())`
7. Fill `speed` with the **median** (1.0), `damage` with the **mode** `df["damage"].mode()[0]` (1.0), and `spawn_weight` with the **median** (15.0). Comment the reasons: the median isn't pulled by extremes, and damage must be a whole number of lives.
8. `df = df.drop_duplicates(subset=["name"], keep="first")`
9. Save `data/obstacles_clean.csv` (`index=False`) and return the DataFrame.

The expected result is 10 rows, 0 missing values, and numeric columns as float64.

### `load_zones(path=os.path.join("data", "zones.csv"))`
`read_csv` → `sort_values("start_m")` → `to_dict("records")`, then for each zone: `z["allowed"] = z["allowed"].split("|")`.

### `load_all()`
Returns `(items_list, zones_list)`, where `items_list = load_obstacles().to_dict("records")`.

---

## 6. Core game logic (`game.py`)

### Data shapes

```python
item_on_road = {"name": "cow", "kind": "obstacle", "effect": "none", "damage": 1, "points": 15,
                "image": "cow.png", "lane": 2, "y": -80.0, "speed": 3.0}
player = {"lane": 1, "lives": 3, "shield": False, "slow_until": 0}
run = {"id": int, "player": str, "date": "YYYY-MM-DD", "distance": 0.0, "dodge_points": 0,
       "score": 0, "time": 0.0, "zone": "Sitabuldi", "dodged": 0, "powerups": 0,
       "types_dodged": set(), "crashes": []}      # crashes = list of {"obstacle", "zone", "second"}
active = []                                       # list of item_on_road dicts
```

### Functions

- **`current_zone(zones, distance)`**: returns the last zone whose `start_m <= distance`.
- **`pick_item(items, zone)`**
  - Keeps only the items whose `name` is in `zone["allowed"]` (a plain for loop with `in`).
  - Builds `weights = np.array([...spawn_weight...])` and `probs = weights / weights.sum()`.
  - Returns `choices[np.random.choice(len(choices), p=probs)]`.
- **`spawn(item, zone)`**: returns a new dictionary with `lane = int(np.random.randint(0, 4))`, `y = -80`, and `speed = BASE_SPEED * item["speed"] * zone["speed_mult"]`.
- **`move_items(active, slow_factor, run)`**
  - Moves every item down with `y += speed * slow_factor`.
  - An obstacle with `y > SCREEN_H` counts as dodged: add its points, increase `dodged`, and add its name to `types_dodged`.
  - Returns `(still_on_screen, dodge_points)`. Build a **new** list rather than removing items while looping; leave a comment explaining why.
- **`check_hits(player, active, run)`**
  - Player rect: `pygame.Rect(LANES[lane] - 25, PLAYER_Y, 50, 80)`. Item rect: `pygame.Rect(LANES[it["lane"]] - 30, it["y"], 60, 60)`.
  - On `colliderect`:
    - a power-up calls `apply_powerup` and does `powerups += 1`
    - with the shield on, the shield is turned off
    - otherwise `lives -= damage` and a crash dict is appended
  - The touched item is removed. Returns the remaining list.
- **`apply_powerup(player, effect)`**
  - `shield` sets `player["shield"] = True`.
  - `slow` sets `slow_until = now + SLOW_MS`.
  - `life` sets `lives = min(lives + 1, MAX_LIVES)`.

### Each frame of play (in `main.py`)

1. Read KEYDOWN events. LEFT moves the player one lane left (if `lane > 0`); RIGHT moves one lane right (if `lane < 3`). Use **KEYDOWN, not `get_pressed`**, so one tap moves exactly one lane.
2. `zone = current_zone(zones, run["distance"])`, then `run["zone"] = zone["zone"]`.
3. `run["distance"] += 0.25 * zone["speed_mult"]`, and `run["time"]` increases by the frame time in seconds.
4. If `now - last_spawn > zone["spawn_gap_ms"]`, spawn one item.
5. `slow_factor = SLOW_FACTOR if now < player["slow_until"] else 1`
6. `move_items`, then `check_hits`.
7. `run["score"] = int(run["distance"]) + run["dodge_points"]`
8. If `lives <= 0`, save the run, compute the report and switch to `"report"`.

The road background scrolls by moving the dashed lane lines down each frame and wrapping them around.

---

## 7. Screens (`main.py`)

A `state` string decides what to draw:

- **`"menu"`**: Title "Nagpur Traffic Dash", a text box where the player types a name (letters, digits and spaces, max 12 characters, Backspace works), the controls, "Enter = ride", "L = leaderboard".
- **`"play"`**: The road, lane lines, items and scooter. The HUD bar on top shows Score, hearts for lives, distance in km (1 decimal place), zone name, "Helmet ON" when shielded, and a "Chai: slow traffic" indicator while it lasts. Briefly flash "Entering Dharampeth!" when the zone changes.
- **`"report"`**: The Run Report (Section 8). "R = ride again", "M = menu".
- **`"leaderboard"`**: Top 5 rows of `runs.csv` sorted by score: player, score, zone reached. "M = menu".

The game loop shape must be obvious:

```python
while running:
    # 1. EVENTS
    # 2. UPDATE  (depends on state)
    # 3. DRAW    (depends on state)
    pygame.display.flip()
    clock.tick(FPS)
```

Load images and fonts **once**, before the loop.

---

## 8. Saving and the Run Report (`report.py`)

### `save_run(run)`
- Appends one line to `data/runs.csv` using `open(path, "a")`, writing the header only if `not os.path.exists(path)`:
  `run_id,player,date,distance_m,score,time_s,zone_reached,dodged,powerups,crashes`
- Appends **one line per crash** to `data/crashes.csv` the same way:
  `run_id,obstacle,zone,second`
- Builds each line with `"{},{},...\n".format(...)`. Strip commas out of player names.
- `run_id`: 1 + the number of rows already in `runs.csv`, or 1 if the file doesn't exist.

### `run_report(run, items)`
Returns a dictionary, using `scores = np.array(pd.read_csv(runs.csv)["score"])`:
- `games`, `best = scores.max()`, `average`, `median`, `consistency = scores.std()`
- `better_than = round((scores < run["score"]).mean() * 100)`
- `top10_score = np.percentile(scores, 90)`
- `improvement = scores[-5:].mean() - scores[:5].mean()`, only when there are 10 or more runs
- `types_dodged = len(run["types_dodged"])`, and `never_dodged` = the set of all obstacle names minus `run["types_dodged"]`
- `top_crashes = crashes.groupby("obstacle").size().sort_values(ascending=False).head(3)`

Handle the edge cases: the first ever run, and no crashes file yet.

### Drawing the report
Draw text rows for each statistic. Add a horizontal bar chart of the top 3 crash obstacles, drawn with `pygame.draw.rect`, with the longest bar 130 px and the others scaled to it.

---

## 9. `analysis.ipynb`

A clean notebook with a markdown heading before every cell explaining what it does. It reads `data/runs.csv` and `data/crashes.csv`. If they are missing, it generates **clearly-labelled simulated demo data** so the notebook runs before anyone has played; mark this loudly as "SIMULATED – replace by playing the game".

Sections, in order:
1. **Load and inspect:** `shape`, `dtypes`, `head(4)`, `tail(4)` of both files.
2. **Cleaning demo:** call `load_obstacles`; show the raw file, `isnull().sum()` before and after, `dtypes` before and after, and the clean table.
3. **Descriptive stats:** `describe()`, mean, median, mode, var and skew of score, distance_m and time_s.
4. **Group analysis:** crashes per obstacle and per zone; average score and time per `zone_reached`.
5. **Extremes:** best and worst runs (`idxmax` / `idxmin`); leaderboard via `sort_values`.
6. **Correlation:** a `corr()` matrix of score, time_s, dodged, powerups and crashes.
7. **Pearson r by hand** for `powerups` vs `score`, using `r = (nΣxy − ΣxΣy) / sqrt((nΣx² − (Σx)²)(nΣy² − (Σy)²))` with NumPy, then compared with `.corr()`.
8. **New column:** `points_per_sec = score / time_s`; top 5 runs by it.
9. **Improvement:** the average score of the first 5 vs the latest 5 runs.
10. **Findings:** a markdown cell with placeholders for the students to fill in.

---

## 10. README.md (for beginners on Windows)

Explain, step by step and with no assumed knowledge:
- install Python 3.12 with "Add python.exe to PATH" ticked
- open Command Prompt in the folder (type `cmd` in the Explorer address bar)
- `pip install pygame pandas numpy jupyter` (if pygame fails, use `pip install pygame-ce`)
- `python main.py` to run the game
- `jupyter notebook` to open the analysis

Also list the controls, explain where the CSV files are saved, and explain how to add a new obstacle by editing only the CSVs.

---

## 11. Build order and checks

1. `settings.py`, then `data.py`. Run `load_obstacles()` and confirm the expected result in Section 5.
2. `game.py`: write a quick check that calls `pick_item` 10,000 times for Sitabuldi and prints the share of each obstacle. The auto should be about 28% and the helmet about 6%.
3. `main.py`: menu, then play with rectangles only, then add images.
4. `report.py`: play two runs and confirm `runs.csv` and `crashes.csv` are created correctly and the report shows sensible numbers.
5. `analysis.ipynb`: run every cell top to bottom.
6. `README.md`.

After each file, give the students a short **beginner-level explanation of what the file does**, function by function, so they can study it.
