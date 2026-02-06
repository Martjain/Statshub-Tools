import csv
import json
import os


def derive_alt_output_path(output_path: str) -> str:
    if output_path.lower().endswith(".json"):
        return output_path[:-5] + ".csv"
    if output_path.lower().endswith(".csv"):
        return output_path[:-4] + ".json"
    return output_path + ".csv"


def save_results(all_collected_data: dict, output_path: str) -> None:
    try:
        if not output_path:
            return
        out_dir = os.path.dirname(output_path) or "."
        os.makedirs(out_dir, exist_ok=True)

        if output_path.lower().endswith(".csv"):
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "team",
                        "stat",
                        "position",
                        "total",
                        "average",
                        "highest",
                        "no_data",
                    ]
                )
                for team, stats_dict in all_collected_data.items():
                    for stat_name, positions in stats_dict.items():
                        for pos in positions:
                            writer.writerow(
                                [
                                    team,
                                    stat_name,
                                    pos.get("position", ""),
                                    pos.get("total", ""),
                                    pos.get("average", ""),
                                    pos.get("highest", ""),
                                    bool(pos.get("no_data", False)),
                                ]
                            )
        else:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(all_collected_data, f, ensure_ascii=False, indent=2)

        print(f"✅ Saved results to {output_path}")
    except Exception as e:
        print(f"⚠️ Failed saving results to {output_path}: {e}")
