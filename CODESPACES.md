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
- ✅ Install all dependencies from `requirements.txt`
- ✅ Configure git with your GitHub identity

**Expected setup time:** 1-2 minutes

You'll see this in the terminal:
```
Running postCreateCommand...
pip install -r requirements.txt
...
Successfully installed haversine-2.8.1 uszipcode-1.0.1 ...
```

### 3. Verify Your Environment

Once the terminal prompt appears, verify the setup:

```bash
# Check Python version (should be 3.12.x)
python --version

# Verify dependencies are installed
pip list | grep haversine
pip list | grep uszipcode

# List repository contents
ls -la
```

### 4. Set Up Data Directory

All input and output files should be stored in the `.data/` directory (git-ignored for privacy):

```bash
# Create the data directory
mkdir -p .data

# Verify it's git-ignored
git check-ignore .data  # Should output: .data
```

**Place your input files here:**
- `.data/teams.csv` — Team roster with numbers, names, zip codes
- `.data/leagues.csv` — League/event information with locations
- `.data/preferences.csv` — Team event preference submissions (optional)

**Example file structure:**
```
FTC-WA-EventAssignment/
├── .data/                    # Your local data (git-ignored)
│   ├── teams.csv
│   ├── leagues.csv
│   ├── preferences.csv
│   └── output/               # Generated assignments
├── .devcontainer/
│   └── devcontainer.json
├── model/
├── assign_home_leagues.py
└── process_event_preferences.py
```

## Running the Assignment Workflow

### Step 1: Assign Home Leagues

Assigns teams to their closest league based on geographic proximity:

```bash
python assign_home_leagues.py \
  --teams .data/teams.csv \
  --leagues .data/leagues.csv \
  --output .data/output/home_leagues.csv
```

**What this does:**
- Calculates distances between team locations and league venues using the haversine formula
- Assigns each team to the nearest league as their "home league"
- Outputs a CSV with team-to-league assignments

### Step 2: Process Event Preferences

Assigns teams to final events based on submitted preferences:

```bash
python process_event_preferences.py \
  --home-leagues .data/output/home_leagues.csv \
  --preferences .data/preferences.csv \
  --leagues .data/leagues.csv \
  --output .data/output/final_assignments.csv
```

**What this does:**
- Processes submitted event preferences (prioritized 1→N)
- Assigns teams to their highest-available preference
- Falls back to home league if all preferences are full
- Handles edge cases (no preferences submitted, all choices unavailable)

### Step 3: Review Outputs

Generated files in `.data/output/`:
- `home_leagues.csv` — Initial proximity-based assignments
- `final_assignments.csv` — Final event assignments incorporating preferences
- Any validation reports or logs

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

This repository's devcontainer configuration defaults to a **2-core/8GB RAM** machine. For this project's workload (CSV processing, distance calculations), the default machine is sufficient.

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
- `.data/` — Your input/output files (teams, preferences, assignments)
- `data/` — Legacy data directory
- `output/` — Generated files

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

Add to `postCreateCommand` in `.devcontainer/devcontainer.json`:

```json
{
  "postCreateCommand": "pip install -r requirements.txt && pip install pandas matplotlib"
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
