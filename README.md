# Nagpur Traffic Dash

A lane-based endless-runner game made with Pygame. Dodge traffic on Nagpur's roads,
pick up power-ups, and see your Run Report at the end of every ride.

This is a Software Lab miniproject for 2nd-year B.Tech (CSE) students.

---

## 1. What you need

- Windows 10 or 11
- Python 3.12, installed from [python.org](https://www.python.org/downloads/)

## 2. Install Python (one time only)

1. Download Python 3.12 from python.org.
2. Run the installer.
3. **Tick the box "Add python.exe to PATH"** at the bottom of the first screen.
4. Click "Install Now".

## 3. Open the project folder in Command Prompt

1. Open the folder `Traffic_Dash` in File Explorer.
2. Click the address bar at the top, type `cmd`, and press Enter.
   A black Command Prompt window opens already inside the folder.

## 4. Install the libraries (one time only)

Type this and press Enter:

```
pip install pygame pandas numpy jupyter
```

If `pygame` fails to install, use this instead:

```
pip install pygame-ce pandas numpy jupyter
```

## 5. Run the game

In the same Command Prompt window, type:

```
python main.py
```

Press Enter. The game window opens.

## 6. Open the analysis notebook

```
jupyter notebook
```

A web page opens. Click `analysis.ipynb`, then run each cell from top to bottom.
If you have not played yet, the notebook uses simulated demo data, marked clearly as
"SIMULATED".

---

## Controls

| Key | Where | What it does |
|-----|-------|--------------|
| Type letters, digits, spaces | Menu | Enter your name (up to 12 characters) |
| Backspace | Menu | Delete a character |
| Enter | Menu | Start a ride |
| L | Menu, name box empty | Open the leaderboard |
| Left / Right arrows | Ride | Move one lane left or right |
| R | Report | Ride again |
| M | Report, leaderboard | Go back to the menu |

## Where the data is saved

The game writes its files into the `data` folder:

- `data/runs.csv`: one line for every ride (score, distance, time, zone reached and so on)
- `data/crashes.csv`: one line for every crash
- `data/obstacles_clean.csv`: the cleaned obstacle list, made each time the game starts

`runs.csv` and `crashes.csv` are created the first time you finish a ride.

## Adding a new obstacle (edit only the CSV files)

You never need to change the Python code to add an obstacle.

1. Open `data/obstacles_raw.csv` in Excel or Notepad.
2. Add a new line with the same columns:
   `name,kind,image,speed,damage,points,spawn_weight,effect`
   For example: `auto_rickshaw,obstacle,rickshaw.png,1.1,1,10,20,none`
3. Open `data/zones.csv` and add the new name to the `allowed` list of each zone
   where it should appear. Separate names with `|`.
4. (Optional) Put a PNG of the object in the `assets` folder with the same file name.
   If you skip this, the game draws a coloured box with the name on it.
5. Run `python main.py` again.

Do not use commas inside a name, and do not leave out the header line.

---

## Project files

| File | Job |
|------|-----|
| `main.py` | Starts the game, runs the game loop and draws the screens |
| `settings.py` | Constants: screen size, speeds, lives, colours |
| `data.py` | Loads and cleans the CSV files |
| `game.py` | Spawning, moving, collisions and power-ups |
| `report.py` | Saves rides and works out the Run Report |
| `analysis.ipynb` | Analysis of the play data |
| `data/` | The CSV files |
| `assets/` | Optional PNG images |
