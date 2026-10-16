# GitHub Codespaces Setup Guide

## What is GitHub Codespaces?

GitHub Codespaces provides a complete, cloud-based development environment that runs in your browser. No local Python installation required — everything runs in a pre-configured container with all dependencies installed.

## Quick Start

### 1. Launch a Codespace

**From GitHub.com:**
1. Navigate to https://github.com/eastmk-goblin-mode/FTC-WA-EventAssignment
2. Click the green **Code** button
3. Select the **Codespaces** tab
4. Click **Create codespace on [branch-name]**

**From VS Code Desktop:**
1. Install the [GitHub Codespaces extension](https://marketplace.visualstudio.com/items?itemName=GitHub.codespaces)
2. Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux)
3. Type "Codespaces: Create New Codespace"
4. Select this repository

### 2. Wait for Environment Setup

The codespace will automatically:
- ✅ Create a Python 3.12 container
- ✅ Install `osmium-tool` (used only for drive-time mode) and the dependencies in `requirements.txt`
- ✅ Run `setup.sh`, which creates `.data/` and builds `.data/zips.csv` for the states in `region.env`
- ✅ Configure git with your GitHub identity

**Expected setup time:** 1-2 minutes

You'll see this in the terminal:
```
Running postCreateCommand...
...
Successfully installed haversine-2.8.1 prettytable-3.10.2 ...
=== Setting up team sorter ===
Wrote .data/zips.csv: 1225 zips (WA 733, OR 492).
✓ Zip table built for the states in region.env
```

If setup prints "Could not build the zip table (no network?)", it fell back to `reference/wa_zips.csv`, which covers Washington only. Rerun `bash setup.sh` once the codespace has network access.

### 3. Verify Your Environment

Once the terminal prompt appears, verify the setup:

```bash
# Check Python version (should be 3.12.x)
python --version

# Verify the zip table was built
head -3 .data/zips.csv

# Run the test suite (standard library only, takes about a second)
python3 -m unittest discover -s tests -t .
```

### 4. Add Your Input Files

All input and output files go in the `.data/` directory, which `setup.sh` created and git ignores:

```bash
# Verify it's git-ignored
git check-ignore .data  # Should output: .data
```

**Place your input files here** (drag and drop into the VS Code file explorer):
- `.data/teams.csv` — `team_number,team_name,zip_code`, no header row
- `.data/events.csv` — `event_code,event_zip,capacity`, no header row
- `.data/pre-assignments.csv` — `event_code,team_number` (optional; lines starting with `#` are comments)

**Example file structure:**
```
FTC-WA-EventAssignment/
├── .data/                    # Your local data (git-ignored)
│   ├── teams.csv
│   ├── events.csv
│   ├── pre-assignments.csv   # optional
│   ├── zips.csv              # built by setup.sh
│   ├── zip_states.csv        # built by setup.sh
│   └── drive_matrix.csv      # built by tools/enable_drive_times.sh (optional)
├── .devcontainer/
│   └── devcontainer.json
├── region.env                # which states are covered
├── reference/wa_zips.csv     # offline fallback zip table (Washington only)
├── sorter/                   # the team sorter
├── tests/
└── tools/                    # zip table, OSRM and drive matrix builders
```

## Running the Sorter

### Step 1: Sort Teams

```bash
python3 -m sorter.cli --program FLL \
  --teams .data/teams.csv \
  --events .data/events.csv \
  --pre-assignments .data/pre-assignments.csv \
  --out .data/team_assignments.csv
```

**What this does:**
- Groups teams by zip code and places each group at the nearest event with room
- Uses drive minutes if `.data/drive_matrix.csv` exists, otherwise straight-line miles
- Writes one row per team with its event, coordinates, travel time or distance, `status` and `flag_reason`

### Step 2: Review the Output

Every input team appears in `.data/team_assignments.csv` as one of:
- `assigned` — placed at an event
- `flagged` — placed, but travel is over the `--flag-over` threshold (default 90), so check it
- `unassigned` — not placed; `flag_reason` says why and what to fix (see the README's "When teams come back unassigned")

The command exits with code 1 when any team is unassigned, so an incomplete run isn't mistaken for a finished one.

### Optional: Drive Times

```bash
bash tools/enable_drive_times.sh
```

This downloads the OpenStreetMap extract for each state in `region.env`, builds a local OSRM routing server, and writes `.data/drive_matrix.csv`. Rerun the sorter afterwards. See the memory note under [Machine Types & Performance](#machine-types--performance) before running it on the default machine.

Kevin's original scripts (`assign_home_leagues.py`, `process_event_preferences.py`) read hardcoded paths under `./data/` and need the `uszipcode` package, which fails on Python 3.12, so they don't run in this codespace.

## Cost Management & Free Tier

### Free Tier Limits (Personal GitHub Account)

| Plan | Storage/Month | Compute Hours/Month |
|------|---------------|---------------------|
| GitHub Free | 15 GB | 120 core-hours |
| GitHub Pro | 20 GB | 180 core-hours |

**What this means:**
- **120 core-hours = 60 real hours** on the default 2-core machine
- Storage is **free** for containers built from the default Python image (which this repo uses)
- Compute charges only when the codespace is **active** (running code or open in your editor)

### Cost-Saving Best Practices

1. **Use the default 2-core machine** (automatically selected by the devcontainer config)
   - Don't manually upgrade to 4-core or 8-core unless you have a specific performance need
   - The default is sufficient for this project's Python scripts

2. **Set an idle timeout:**
   - Go to https://github.com/settings/codespaces
   - Set "Default idle timeout" to **30 minutes** (or as low as 5 minutes)
   - Codespaces will auto-stop when inactive, preserving your compute hours

3. **Delete unused codespaces:**
   - Each codespace consumes storage even when stopped
   - Delete old/finished codespaces from https://github.com/codespaces
   - Alternatively, set "Default retention period" to 7 days for automatic cleanup

4. **Stop your codespace when done:**
   - Click the codespace name in the bottom-left corner
   - Select "Stop Current Codespace"
   - Or close the browser tab — it will auto-stop after the idle timeout

5. **Monitor your usage:**
   - View current usage: https://github.com/settings/billing/summary
   - Set spending limits: https://github.com/settings/billing/spending_limit

## Machine Types & Performance

This repository's devcontainer configuration defaults to a **2-core/8GB RAM** machine. For sorting teams (CSV processing, straight-line distances, reading a drive matrix), the default machine is sufficient.

**Drive-time mode needs more memory to build than to use.** Building the OSRM routing graph peaked at 4.7 GB of RAM for Washington alone and 6.4 GB for Washington plus Oregon (measured on macOS). That leaves little room on an 8 GB machine, and the build may fail. Two ways to handle it:
- Build `.data/drive_matrix.csv` on a computer with more memory, then upload only that file into `.data/` in the codespace. The sorter reads it the same way, and the codespace stays on the default machine.
- Switch to a 4-core/16 GB machine for the build, at twice the cost, then switch back.

The drive matrix only needs rebuilding when the teams or events change.

**Available machine types:**
| Cores | RAM | Storage | Cost Multiplier |
|-------|-----|---------|-----------------|
| 2-core | 8 GB | 32 GB | 1x (baseline) |
| 4-core | 16 GB | 32 GB | 2x |
| 8-core | 32 GB | 64 GB | 4x |

**When to upgrade:**
- Processing very large datasets (thousands of teams)
- Running multiple heavy operations simultaneously
- Performance is noticeably slow on the default machine

**How to change machine type:**
1. Click the codespace name in bottom-left corner
2. Select "Change Machine Type"
3. Choose a larger machine (will restart the codespace)

## Troubleshooting

### Codespace Won't Start

**Symptom:** Stuck on "Creating codespace..." or "Setting up..."

**Solutions:**
1. Wait 5 minutes — initial setup can be slow
2. Check [GitHub Status](https://www.githubstatus.com/) for service outages
3. Try creating a new codespace (delete the stuck one first)
4. Check your account's storage/compute limits aren't exceeded

### Dependencies Not Installed

**Symptom:** `ModuleNotFoundError: No module named 'haversine'`

**Solutions:**
1. Manually install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Rebuild the container:
   - Press `Cmd+Shift+P` / `Ctrl+Shift+P`
   - Type "Codespaces: Rebuild Container"
   - Select "Rebuild Container" (will re-run setup)

### Git Identity Issues

**Symptom:** `Author identity unknown` when committing

**Solutions:**
```bash
git config --global user.email "your-email@example.com"
git config --global user.name "Your Name"
```

Or configure in your GitHub account settings to apply to all codespaces automatically.

### Data Files Not Found

**Symptom:** `FileNotFoundError: .data/teams.csv`

**Check:**
1. Verify the `.data/` directory exists: `ls -la .data/`
2. Confirm files are uploaded (drag-and-drop into VS Code file explorer)
3. Check file paths in your commands match the actual file names

**Symptom:** `Warning: .data/zips.csv not found; using reference/wa_zips.csv`

**Fix:** Run `bash setup.sh`. It needs network access to download the zip database the first time.

### Out of Storage/Compute Hours

**Symptom:** "You have exceeded your storage/compute quota"

**Solutions:**
1. Delete old codespaces: https://github.com/codespaces
2. Wait until next monthly billing cycle (quota resets)
3. Add a payment method and set spending limit
4. Upgrade to GitHub Pro for higher free tier limits

## Privacy & Data Security

### What's Git-Ignored

The `.gitignore` file prevents these from being committed:
- `.data/` — Your input/output files (teams, events, assignments, drive matrix)
- `data/` — Legacy data directory used by Kevin's original scripts
- `output/` — Generated files
- `formatted_combined_run/` — Local run output

**Before committing:**
```bash
# Verify sensitive files are ignored
git status

# Should NOT see .data/ files listed
# If they appear, they're not being ignored — stop and verify .gitignore
```

### Best Practices

1. **Never commit real team/student data** to a public repository
2. Use **sample/anonymized data** for testing in public repos
3. Keep the `.data/` directory for **all real data files**
4. Review `git status` before every commit

## Advanced: Customizing Your Codespace

### Installing Additional Tools

Append to the existing `postCreateCommand` in `.devcontainer/devcontainer.json`:

```json
{
  "postCreateCommand": "sudo apt-get update -qq && sudo apt-get install -y -qq osmium-tool && pip install -r requirements.txt && bash setup.sh && pip install pandas matplotlib"
}
```

### Adding VS Code Extensions

Add to `.devcontainer/devcontainer.json`:

```json
{
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance"
      ]
    }
  }
}
```

### Changing Python Version

Update the `image` in `.devcontainer/devcontainer.json`:

```json
{
  "image": "mcr.microsoft.com/devcontainers/python:3.13"
}
```

Then rebuild the container.

## Resources

- **GitHub Codespaces Docs:** https://docs.github.com/en/codespaces
- **Pricing Calculator:** https://github.com/pricing/calculator
- **Billing Overview:** https://docs.github.com/en/billing/managing-billing-for-github-codespaces
- **Dev Container Spec:** https://containers.dev/

## Getting Help

1. Check this guide's Troubleshooting section
2. Review GitHub's [Codespaces documentation](https://docs.github.com/en/codespaces)
3. Open an issue in this repository
4. Ask in the FTC Washington community channels

---

**Ready to get started?** [Launch a codespace →](https://github.com/eastmk-goblin-mode/FTC-WA-EventAssignment/codespaces)
