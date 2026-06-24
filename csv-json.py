import json
import os
import pandas as pd


def parse_ipl_json_for_crunch(input_folder, output_csv_path):
    all_deliveries = []

    print("Parsing nested JSON data to match IPL Crunch '26 requirements...")

    if not os.path.exists(input_folder):
        print(f"Error: The folder '{input_folder}' does not exist.")
        return

    # Loop through every JSON file in the folder
    for filename in os.listdir(input_folder):
        if filename.endswith(".json"):
            file_path = os.path.join(input_folder, filename)

            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except Exception as e:
                    print(f"Skipping broken file {filename}: {e}")
                    continue

                match_id = filename.replace(".json", "")

                # 1. Extract Match Metadata ('info' block)
                info = data.get("info", {})
                season = info.get("season", "Unknown")

                # Toss details
                toss = info.get("toss", {})
                toss_winner = toss.get("winner", None)
                toss_decision = toss.get("decision", None)

                # Winner details
                outcome = info.get("outcome", {})
                winner = outcome.get("winner", None)

                # Fallback if match was tied/abandoned without a specific team winning
                if not winner and "result" in outcome:
                    winner = outcome.get("result")

                # 2. Extract Innings & Delivery Details
                innings_list = data.get("innings", [])

                # Use enumerate to track 1st vs 2nd innings (1-indexed)
                for inn_idx, inning_data in enumerate(innings_list, start=1):
                    team_name = inning_data.get("team")
                    overs_list = inning_data.get("overs", [])

                    for over_data in overs_list:
                        over_number = over_data.get("over")  # 0-indexed
                        deliveries = over_data.get("deliveries", [])

                        for ball_idx, delivery in enumerate(deliveries):
                            runs = delivery.get("runs", {})
                            wicket_list = delivery.get("wickets", [])
                            wkt = (
                                wicket_list[0] if len(wicket_list) > 0 else {}
                            )

                            # Create flat dictionary using raw names
                            # The renames mapping in your script will handle the rest!
                            flat_delivery = {
                                "match_id": match_id,
                                "season": season,
                                "toss_winner": toss_winner,
                                "toss_decision": toss_decision,
                                "winner": winner,
                                "innings": inn_idx,
                                "batting_team": team_name,
                                "over": over_number
                                + 1,  # Standardizes 0-19 to 1-20
                                "striker": delivery.get("batter"),
                                "bowler": delivery.get("bowler"),
                                "non_striker": delivery.get("non_striker"),
                                "runs_off_bat": runs.get("batter", 0),
                                "extras_runs": runs.get("extras", 0),
                                "runs_total": runs.get("total", 0),
                                "player_dismissed": wkt.get(
                                    "player_out", None
                                ),
                                "dismissal_kind": wkt.get("kind", None),
                            }
                            all_deliveries.append(flat_delivery)

    if not all_deliveries:
        print("No match deliveries extracted.")
        return

    # Create DataFrame and save
    df = pd.DataFrame(all_deliveries)
    df.to_csv(output_csv_path, index=False)
    print(
        f"Successfully written {len(df):,} delivery rows to '{output_csv_path}'."
    )


# --- Execution Path ---
folder_path = "./ipl_json"
output_file = "./ipl_matches.csv"

parse_ipl_json_for_crunch(folder_path, output_file)