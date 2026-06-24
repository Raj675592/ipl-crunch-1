"""
cricsheet_loader.py
===================
Converts Cricsheet JSON or YAML match files (one file per match)
into the two flat DataFrames used by ipl_analysis.py:
  - matches.csv    (one row per match)
  - deliveries.csv (one row per ball)

Usage
-----
  # Convert a folder of JSON files:
  python cricsheet_loader.py --folder ./ipl_json  --format json

  # Convert a folder of YAML files:
  python cricsheet_loader.py --folder ./ipl_yaml  --format yaml

  # Auto-detect format from extension:
  python cricsheet_loader.py --folder ./ipl_data

  # Then run the main analysis:
  python ipl_analysis.py matches.csv deliveries.csv

Cricsheet JSON/YAML structure (key paths used)
----------------------------------------------
info.season          → season
info.teams           → team1, team2
info.toss.winner     → toss_winner
info.toss.decision   → toss_decision
info.outcome.winner  → match_winner  (absent if no result / tie)
info.venue           → venue
info.dates[0]        → date
innings[n].team      → batting_team
innings[n].overs[o].deliveries[d].batter      → batter
innings[n].overs[o].deliveries[d].bowler      → bowler
innings[n].overs[o].deliveries[d].runs.batter → batsman_runs
innings[n].overs[o].deliveries[d].runs.total  → total_runs
innings[n].overs[o].deliveries[d].wickets     → player_dismissed
"""

import os
import sys
import json
import glob
import argparse
import pandas as pd

try:
    import yaml
    YAML_OK = True
except ImportError:
    YAML_OK = False


# ── Loaders ───────────────────────────────────────────────────────────────────

def load_file(path: str) -> dict:
    """Load a single Cricsheet JSON or YAML match file."""
    ext = os.path.splitext(path)[1].lower()
    with open(path, "r", encoding="utf-8") as f:
        if ext == ".json":
            return json.load(f)
        elif ext in (".yaml", ".yml"):
            if not YAML_OK:
                raise ImportError("PyYAML not installed. Run: pip install pyyaml")
            return yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported extension: {ext}")


# ── Parsers ───────────────────────────────────────────────────────────────────

def parse_match(data: dict, match_id: int) -> dict:
    """Extract one match-level row from a Cricsheet match dict."""
    info    = data.get("meta", {})        # older files use 'meta'
    info    = data.get("info", info)      # prefer 'info'
    outcome = info.get("outcome", {})
    toss    = info.get("toss", {})
    teams   = info.get("teams", [None, None])
    dates   = info.get("dates", [None])

    return {
        "match_id"     : match_id,
        "season"       : info.get("season"),
        "date"         : dates[0] if dates else None,
        "venue"        : info.get("venue"),
        "team1"        : teams[0] if len(teams) > 0 else None,
        "team2"        : teams[1] if len(teams) > 1 else None,
        "toss_winner"  : toss.get("winner"),
        "toss_decision": toss.get("decision"),
        "match_winner" : outcome.get("winner"),      # None if no result / tie
        "result"       : outcome.get("result", "normal"),
        "player_of_match": (info.get("player_of_match") or [None])[0],
    }


def parse_deliveries(data: dict, match_id: int) -> list[dict]:
    """Flatten all deliveries in a match into a list of row dicts."""
    rows = []
    innings_list = data.get("innings", [])

    for inning_num, inning in enumerate(innings_list, start=1):
        batting_team  = inning.get("team", "")
        overs_data    = inning.get("overs", [])

        for over_obj in overs_data:
            over_num      = over_obj.get("over", 0)  # 0-indexed in Cricsheet
            deliveries    = over_obj.get("deliveries", [])

            for ball_num, d in enumerate(deliveries, start=1):
                runs_block = d.get("runs", {})
                extras     = d.get("extras", {})

                # Wicket info
                wickets        = d.get("wickets", [])
                player_dismissed = wickets[0].get("player_out") if wickets else None
                dismissal_kind   = wickets[0].get("kind")       if wickets else None

                rows.append({
                    "match_id"        : match_id,
                    "inning"          : inning_num,
                    "batting_team"    : batting_team,
                    "over"            : over_num + 1,   # convert to 1-indexed
                    "ball"            : ball_num,
                    "batter"          : d.get("batter"),
                    "non_striker"     : d.get("non_striker"),
                    "bowler"          : d.get("bowler"),
                    "batsman_runs"    : runs_block.get("batter", 0),
                    "extras"          : runs_block.get("extras", 0),
                    "total_runs"      : runs_block.get("total", 0),
                    "wides"           : extras.get("wides", 0),
                    "noballs"         : extras.get("noballs", 0),
                    "byes"            : extras.get("byes", 0),
                    "legbyes"         : extras.get("legbyes", 0),
                    "player_dismissed": player_dismissed,
                    "dismissal_kind"  : dismissal_kind,
                })
    return rows


# ── Main converter ────────────────────────────────────────────────────────────

def convert_folder(folder: str,
                   fmt: str = "auto",
                   out_matches: str = "matches.csv",
                   out_deliveries: str = "deliveries.csv"):

    # Find files
    if fmt == "json":
        pattern = "*.json"
    elif fmt in ("yaml", "yml"):
        pattern = "*.yaml"
    else:
        pattern = "*"

    paths = sorted(glob.glob(os.path.join(folder, pattern)))
    # Filter to supported extensions if auto
    paths = [p for p in paths
             if os.path.splitext(p)[1].lower() in (".json", ".yaml", ".yml")]

    if not paths:
        print(f"[ERROR] No JSON/YAML files found in: {folder}")
        sys.exit(1)

    print(f"Found {len(paths):,} match files in '{folder}'")

    match_rows    = []
    delivery_rows = []
    errors        = 0

    for match_id, path in enumerate(paths, start=1):
        try:
            data = load_file(path)
            match_rows.append(parse_match(data, match_id))
            delivery_rows.extend(parse_deliveries(data, match_id))
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"  [WARN] Skipping {os.path.basename(path)}: {e}")

    if errors > 5:
        print(f"  ... and {errors - 5} more warnings suppressed.")

    matches    = pd.DataFrame(match_rows)
    deliveries = pd.DataFrame(delivery_rows)

    matches.to_csv(out_matches, index=False)
    deliveries.to_csv(out_deliveries, index=False)

    print(f"\n✅ Converted successfully:")
    print(f"   matches.csv    → {len(matches):,} matches  ({out_matches})")
    print(f"   deliveries.csv → {len(deliveries):,} deliveries  ({out_deliveries})")
    print(f"   Seasons found  : {sorted(matches['season'].dropna().unique().tolist())}")
    print(f"\nNow run: python ipl_analysis.py {out_matches} {out_deliveries}")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert Cricsheet JSON/YAML match files → matches.csv + deliveries.csv"
    )
    parser.add_argument("--folder",  default=".",
                        help="Folder containing Cricsheet match files (default: current dir)")
    parser.add_argument("--format",  default="auto",
                        choices=["json", "yaml", "yml", "auto"],
                        help="File format to look for (default: auto-detect)")
    parser.add_argument("--out-matches",    default="matches.csv")
    parser.add_argument("--out-deliveries", default="deliveries.csv")
    args = parser.parse_args()

    convert_folder(
        folder        = args.folder,
        fmt           = args.format,
        out_matches   = args.out_matches,
        out_deliveries= args.out_deliveries,
    )