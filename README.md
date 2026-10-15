## FTC Washington Event Assignment

All of the code in this repo is meant to be used for assigning FTC teams to leagues according to the methodology laid out for FTC in Washington. There are two main steps in that as currently planned.

## Setup

### Prerequisites
- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended) or pip

### Option 1: GitHub Codespaces (Recommended)

Launch a pre-configured development environment directly in your browser:

1. **Create a codespace:**
   - Go to https://github.com/eastmk-goblin-mode/FTC-WA-EventAssignment
   - Click the green **Code** button
   - Select the **Codespaces** tab
   - Click **Create codespace on main** (or your working branch)

2. **Wait for setup to complete:**
   - The codespace will automatically install Python 3.12 and all dependencies
   - Setup typically takes 1-2 minutes
   - You'll see "Running postCreateCommand..." in the terminal

3. **Set up your data directory:**
   ```bash
   mkdir -p .data
   # Place your input files (teams, leagues, preferences) in .data/
   ```

4. **Run the assignment workflow:**
   ```bash
   # Example: Assign teams to home leagues
   python assign_home_leagues.py --teams .data/teams.csv --leagues .data/leagues.csv
   
   # Process event preferences
   python process_event_preferences.py --preferences .data/preferences.csv
   ```

**Cost management:**
- Free tier: 120 core-hours/month (60 hours on the default 2-core machine)
- Codespaces auto-stop after 30 minutes of inactivity (configurable in [Settings → Codespaces](https://github.com/settings/codespaces))
- Storage is free for the default dev container configuration

For detailed Codespaces setup and troubleshooting, see [CODESPACES.md](CODESPACES.md).

### Option 2: Local Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/eastmk-goblin-mode/FTC-WA-EventAssignment.git
   cd FTC-WA-EventAssignment
   ```

2. Create and activate a virtual environment:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   uv pip install -r requirements.txt setuptools
   ```

## Assignment Methodology

1. Given a list of leagues and teams, assign teams to leagues based solely on event proximity. The goal here is to determine an optimal set of "Home League" assignments to reduce the overall travel requirements we ask of teams. At least on the initial pass it's unlikely that this will consider inter-team relationships or impassable boundaries (asking teams to drive over water), so manual adjustments may be required. In the given output all teams must have a home-league assignment.

2. Given a list of leagues, teams, home-league asignments, and submitted event preferences (priortized 1->N for a subset of teams), assign teams to their final event assignments. If a team doesn't submit event preferences they will be assigned to their home league. After that, we will go through the event-preference submissions in a deterministic-but-random order to assign teams to their highest-available preference, bypassing any leagues that are full. The edge case where a team doesn't get assigned to an event after submitted preferences needs to be considered, and if the algorithm doesn't assign a team one option could be to fall back on a team's home event.

In addition to the above functionality, there will likely be a script to ensure any submitted event preferences are valid against the public criteria.

## Drive-Time Sorter (FLL)

A new zip-bucket greedy assignment algorithm designed for FLL Washington with support for drive-time routing. Located in the `sorter/` package.

### Quick Start

**Straight-line mode (default, works immediately):**
```bash
python3 -m sorter.cli --teams .data/teams.csv --events .data/events.csv --program FLL
```

**Drive-time mode (optional, one-time setup):**
```bash
# Enable OSRM routing (~3-5 minutes first time)
bash tools/enable_drive_times.sh

# Run with drive times
python3 -m sorter.cli --teams .data/teams.csv --events .data/events.csv --program FLL
```

### Features

- **Program selection (required):**
  - `--program FLL` / `--program FTC` / `--program FRC`
  - Sets the program field in output (required for map visualization)

- **Multiple ordering strategies:**
  - `--method bump` (default): Prioritizes teams with limited venue options
  - `--method largest`: Kevin's largest-zip-first approach (compatible)  
  - `--method regret`: Dynamic regret ordering

- **Distance modes:**
  - Straight-line miles (no setup required)
  - OSRM drive minutes with ferry handling (opt-in via `enable_drive_times.sh`)

- **Pre-assignments:** `--pre-assignments .data/locks.csv` (format: `event_code,team_number`)

- **Map output:** CSV with standardized columns for visualization, status flags, and travel distances

### Algorithm

Zip-bucket greedy: groups teams by zip code and assigns whole groups to events, keeping related teams together. The bump-cost ordering places teams with poor fallback options first, reducing travel for geographically constrained groups.

For methodology details and trade-offs, see the algorithm comparison analysis (to be added).

### File Formats

**Input CSVs:**
- `teams.csv`: `team_number,team_name,zip_code`
- `events.csv`: `event_code,event_zip,capacity`
- `pre-assignments.csv` (optional): `event_code,team_number`

**Output CSV:**
- **Required columns (map team):** `team_id, team_name, team_zipCode, team_coordinates, event_id, event_zipCode, event_coordinates, program`
- **Operational columns:** `miles` (or `drive_minutes`), `status`, `flag_reason`
- Status: `assigned`, `flagged` (over travel threshold), `unassigned` (no room or unknown zip)
- Coordinates use WKT format: `POINT (longitude latitude)`

### Drive-Time Setup

**Requirements for OSRM routing:**
- Docker (Linux/Codespaces) or Homebrew osrm-backend (macOS)
- ~2GB disk for Washington state map data
- ~5GB RAM (4-core/16GB Codespace recommended, 2-core works but slower)

**What happens:**
1. Downloads OpenStreetMap Washington extract (365MB)
2. Builds routing graph (~3-5 minutes)
3. Starts local OSRM server on port 5055
4. Pre-computes drive matrix for all team×event pairs

**Privacy:** All routing happens locally. No team data leaves your machine.

### Testing

Basic smoke test:
```bash
# Should complete in <5 seconds
python3 -m sorter.cli --teams .data/teams.csv --events .data/events.csv --program FLL --out .data/output.csv
echo "Exit code: $?"
```

Compatibility test with Kevin's data (requires fixing uszipcode/sqlalchemy_mate version conflict first):
```bash
python3 assign_home_leagues.py  # Original script should still work
```