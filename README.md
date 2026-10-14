## FTC Washington Event Assignment

All of the code in this repo is meant to be used for assigning FTC teams to leagues according to the methodology laid out for FTC in Washington. There are two main steps in that as currently planned.

## Setup

### Prerequisites
- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended) or pip

### Installation

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