# Known Issues

## uszipcode / sqlalchemy_mate Compatibility (Python 3.12)

**Status:** Workaround in place

**Issue:**  
The `uszipcode==1.0.1` package depends on `sqlalchemy_mate`, which has an `AttributeError` with Python 3.12:
```
AttributeError: module 'sqlalchemy_mate' has no attribute 'ExtendedBase'
```

**Impact:**
- Kevin's original `assign_home_leagues.py` cannot import (uses uszipcode)
- The `tools/build_zip_table.py` script cannot generate zip centroids

**Workaround:**
Use the pre-built `wa_zips.csv` from the prototype project. This file is already in `.data/` and contains all Washington zip centroids needed for sorting.

**Not affected:**
- The new `sorter/` package works fine (doesn't use uszipcode)
- All sorting functionality (straight-line and drive-time modes)
- Map output generation

**Potential fixes:**
1. Downgrade to Python 3.11 (where uszipcode works)
2. Pin `sqlalchemy_mate<1.5` (if compatible version exists)
3. Replace uszipcode with direct `sqlite3` queries against its database
4. Use a different zip lookup library (e.g., `zipcodes`, `uszipcode-alt`)

**For Codespaces:**
The devcontainer uses Python 3.12 and includes the pre-built zip table, so this issue doesn't block usage.

**For local development:**
If you need to regenerate the zip table, either:
- Use Python 3.11 temporarily
- Use the existing `wa_zips.csv` (it rarely changes)
