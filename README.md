# Activity Monitor (Python GUI)

Desktop app to track your sport activities:
- cycling
- hiking
- walking

## Features

- Add activity with:
  - date
  - activity type
  - distance (km)
  - average metric:
    - cycling: speed in km/h
    - hiking/walking: pace in min/km
  - total time
  - calories
- Data persistence in SQLite database (`activities.db`)
- Browse and filter by:
  - activity type
  - date range
  - min/max distance
- Show charts:
  - distance by activity
  - calories by activity
  - monthly distance trend
- Export filtered data to CSV
- Delete selected entries

## Requirements

- Python 3.10+
- `matplotlib` (for charts)

## Universal setup (macOS / Linux / Windows)

1. Open terminal in project folder.
2. (If needed) install Tk support for your Python.
3. Create and activate virtual environment.
4. Install dependencies.
5. Run the app.

### macOS / Linux

```bash
cd /path/to/activitiesmonitor
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python activity_monitor.py
```

### Windows (PowerShell)

```powershell
cd C:\path\to\activitiesmonitor
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python .\activity_monitor.py
```

### If you get `No module named '_tkinter'`

Your Python was built without Tk support.

- macOS (Homebrew Python 3.14):

```bash
brew install python-tk@3.14
```

Then recreate virtual environment:

```bash
cd /path/to/activitiesmonitor
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python activity_monitor.py
```

- Ubuntu/Debian example:

```bash
sudo apt install python3-tk
```

## VS Code one-click run

Use task: **Run Activity Monitor**

- Open Command Palette and run: `Tasks: Run Task`
- Select: `Run Activity Monitor`

## Tests

Run tests:

```bash
python -m pytest -q
```

Notes:
- Tests are in [tests/test_activity_monitor.py](tests/test_activity_monitor.py)
- Database tests use a separate temporary `test.db` file (not your production `activities.db`)

## Input notes

- Date format: `YYYY-MM-DD`
- Distance (km): decimal number (e.g. `12.4`)
- Total time format:
  - `hh:mm`
  - `hh:mm:ss`
  - or minutes as decimal (e.g. `95.5`)
- Pace for hiking/walking:
  - `mm:ss` (e.g. `8:30`)
  - or decimal minutes per km (e.g. `8.5`)
