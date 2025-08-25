import argparse
import os
import importlib.util
import json
import random
import math
import sys
import csv
from main import SnakeGame 
from datetime import datetime
from pathlib import Path


BOTS_DIR = os.path.join(os.path.dirname(__file__), "bots")

# --- Bot Discovery ---
def discover_bots() -> dict:
    """Scan bots folder and return all discovered UserBots with metadata."""
    bots = {}

    if not os.path.exists(BOTS_DIR):
        print(f"[ERROR] Bots folder not found: {BOTS_DIR}")
        sys.exit(1)

    for folder in os.listdir(BOTS_DIR):
        folder_path = os.path.join(BOTS_DIR, folder)
        if not os.path.isdir(folder_path):
            continue

        bot_files = [f for f in os.listdir(folder_path) if f.endswith("_bot.py")]
        if not bot_files:
            print(f"[WARN] No *_bot.py file found in {folder}")
            continue
        bot_file = bot_files[0]

        module_name = f"{folder}.{bot_file[:-3]}"
        module_path = os.path.join(folder_path, bot_file)

        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)  # type: ignore
        except Exception as e:
            print(f"[ERROR] Failed to load {module_path}: {e}")
            continue

        if not hasattr(module, "UserBot"):
            print(f"[WARN] No UserBot class found in {module_path}")
            continue

        UserBot = getattr(module, "UserBot")
        try:
            instance = UserBot()
        except Exception as e:
            print(f"[ERROR] Could not instantiate UserBot from {module_path}: {e}")
            continue

        bots[folder] = {
            "id": folder,
            "file": bot_file,
            "path": module_path,
            "class": "UserBot",
            "name": getattr(instance, "name", "UnnamedBot")
        }

    return bots

def cli_discover(output: str):
    bots = discover_bots()
    if not bots:
        print("No valid bots discovered.")
        return

    print("\n=== Discovered Bots ===")
    for bot_id, meta in bots.items():
        print(f"- {bot_id}: {meta['name']} ({meta['class']}) @ {meta['path']}")
    print("=======================\n")
    print(f"Total bots discovered: {len(bots)}")

    with open(output, "w") as f:
        json.dump(bots, f, indent=4, ensure_ascii=False)
    print(f"Bot metadata saved to {output}")


# --- Tournament Core ---
def generate_tournament_tables(team_ids, group_size):
    teams = team_ids.copy()
    random.shuffle(teams)
    total_teams = len(teams)
    num_groups = math.ceil(total_teams / group_size)
    start_index = 0
    
    data = {"total_teams": total_teams, "group_size": group_size, "groups": {}}
    
    for i in range(num_groups):
        end_index = start_index + group_size
        group_teams = teams[start_index:end_index]
        start_index = end_index
        group_name = chr(65 + i)  # A, B, C...
        
        data["groups"][group_name] = {"standings": {}, "matches": []}
        for team in group_teams:
            data["groups"][group_name]["standings"][team] = {
                "wins": 0, "draws": 0, "losses": 0, "points": 0,
                "goals_for": 0, "goals_against": 0, "goal_diff": 0
            }
        
        n = len(group_teams)
        for j in range(n):
            for k in range(j + 1, n):
                match = {group_teams[j]: {"score": 0}, group_teams[k]: {"score": 0}}
                data["groups"][group_name]["matches"].append(match)
    
    return data

def update_standings(tournament_data):
    for _, group_data in tournament_data["groups"].items():
        standings = group_data["standings"]

        # reset per-team stats before recompute
        for team in standings.keys():
            standings[team].update({
                "wins": 0, "draws": 0, "losses": 0, "points": 0,
                "goals_for": 0, "goals_against": 0, "goal_diff": 0
            })

        # recompute from matches
        for match in group_data["matches"]:
            team1, team2 = list(match.keys())
            score1, score2 = match[team1]["score"], match[team2]["score"]

            standings[team1]["goals_for"] += score1
            standings[team1]["goals_against"] += score2
            standings[team2]["goals_for"] += score2
            standings[team2]["goals_against"] += score1

            if score1 > score2:
                standings[team1]["wins"] += 1
                standings[team1]["points"] += 3
                standings[team2]["losses"] += 1
            elif score2 > score1:
                standings[team2]["wins"] += 1
                standings[team2]["points"] += 3
                standings[team1]["losses"] += 1
            else:
                standings[team1]["draws"] += 1
                standings[team2]["draws"] += 1
                standings[team1]["points"] += 1
                standings[team2]["points"] += 1

        # compute goal_diff after all matches
        for team in standings.keys():
            standings[team]["goal_diff"] = standings[team]["goals_for"] - standings[team]["goals_against"]

    return tournament_data

def knockout_stage(qualified_teams, report_dir="reports"):
    """
    Run single elimination knockout until one champion remains.
    qualified_teams: list of UserBot objects.
    """
    round_number = 1
    while len(qualified_teams) > 1:
        print(f"\n--- Knockout Round {round_number} ---")
        next_round = []
        
        # Shuffle for fairness if needed
        random.shuffle(qualified_teams)

        # Pair matches
        for i in range(0, len(qualified_teams), 2):
            if i + 1 >= len(qualified_teams):
                # Odd number of teams -> auto-qualify
                print(f"{qualified_teams[i].name} advances by default.")
                next_round.append(qualified_teams[i])
                continue

            bot1, bot2 = qualified_teams[i], qualified_teams[i+1]
            print(f"\n🎮 Match: {bot1.name} vs {bot2.name}")

            # Run the match using your existing SnakeGame
            game = SnakeGame(bot1.__class__, bot2.__class__)
            winner_name = game.run()  # make sure your run() returns winner's name

            if winner_name == bot1.name:
                next_round.append(bot1)
            else:
                next_round.append(bot2)
        
        qualified_teams = next_round
        round_number += 1

    champion = qualified_teams[0]
    print(f"\n🏆 Champion: {champion.name} 🏆")
    return champion

def k_best(k, tournament):
    teams = []
    for _, group in tournament["groups"].items():
        for team_name, team in group["standings"].items():
            teams.append((team_name, team["points"]))
    sorted_teams = sorted(teams, key=lambda x: x[1], reverse=True)
    return [team[0] for team in sorted_teams[:k]]


def load_bots_from_folder(bots_dir: str = "bots"):
    """Dynamically load UserBot classes from bots subfolders."""
    bots = []
    bots_path = Path(bots_dir)

    for bot_file in bots_path.rglob("*_bot.py"):
        module_name = bot_file.stem  # e.g., "alice_bob_bot"
        spec = importlib.util.spec_from_file_location(module_name, bot_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, "UserBot"):
            bot_class = getattr(module, "UserBot")
            bots.append(bot_class())
        else:
            print(f"⚠️ Skipped {bot_file} (no UserBot class found)")
    return bots


# --- CLI ---

def cli_show(input_file: str):
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    rows = compute_leaderboard(data)
    print_leaderboard(rows)


def compute_leaderboard(data):
    """Return a global leaderboard list of dicts: one row per team with group info."""
    update_standings(data)
    rows = []
    for group_name, group in data["groups"].items():
        for team, s in group["standings"].items():
            row = {
                "team": team,
                "group": group_name,
                "points": s["points"],
                "wins": s["wins"],
                "draws": s["draws"],
                "losses": s["losses"],
                "goals_for": s["goals_for"],
                "goals_against": s["goals_against"],
                "goal_diff": s["goal_diff"],
            }
            rows.append(row)
    rows.sort(key=lambda r: (r["points"], r["goal_diff"], r["goals_for"]), reverse=True)
    return rows


def print_leaderboard(rows):
    """Pretty print a global leaderboard with rank and group."""
    print("\n=== Leaderboard (Global) ===")
    header = f"{'Rank':>4}  {'Team':<35} {'Grp':>3} {'Pts':>3} {'W':>2} {'D':>2} {'L':>2} {'GF':>3} {'GA':>3} {'GD':>3}"
    print(header)
    print("-" * len(header))
    for idx, r in enumerate(rows, 1):
        print(f"{idx:>4}  {r['team']:<35} {r['group']:>3} {r['points']:>3} {r['wins']:>2} {r['draws']:>2} {r['losses']:>2} "
              f"{r['goals_for']:>3} {r['goals_against']:>3} {r['goal_diff']:>3}")

def export_csv(rows, output_path: str):
    """Export leaderboard rows to CSV."""
    fieldnames = ["rank", "team", "group", "points", "wins", "draws", "losses",
                  "goals_for", "goals_against", "goal_diff"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for idx, r in enumerate(rows, 1):
            writer.writerow({
                "rank": idx,
                **r
            })


def export_markdown(rows, output_path: str):
    """Export leaderboard rows to Markdown table."""
    lines = []
    lines.append("| Rank | Team | Group | Pts | W | D | L | GF | GA | GD |")
    lines.append("|---:|:-----|:----:|---:|--:|--:|--:|---:|---:|---:|")
    for idx, r in enumerate(rows, 1):
        lines.append(f"| {idx} | {r['team']} | {r['group']} | {r['points']} | {r['wins']} | {r['draws']} | {r['losses']} | "
                     f"{r['goals_for']} | {r['goals_against']} | {r['goal_diff']} |")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def cli_report(input_file: str, out_json: str, out_csv: str = "", out_md: str = ""):
    """Create a final snapshot JSON + optional CSV/Markdown exports and print leaderboard."""
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # ensure standings are current
    update_standings(data)
    leaderboard = compute_leaderboard(data)

    # final snapshot
    snapshot = {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "total_teams": data.get("total_teams"),
        "group_size": data.get("group_size"),
        "groups": data["groups"],      # contains updated standings + matches
        "leaderboard": leaderboard,    # global leaderboard (sorted)
    }

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=4, ensure_ascii=False)
    print(f"✅ Final JSON saved to {out_json}")

    # pretty print
    print_leaderboard(leaderboard)

    # optional exports
    if out_csv:
        export_csv(leaderboard, out_csv)
        print(f"📄 CSV saved to {out_csv}")
    if out_md:
        export_markdown(leaderboard, out_md)
        print(f"📝 Markdown saved to {out_md}")


def cli_play(input_file: str, output_file: str = "", headless: bool = False):
    """Play all matches in a tournament JSON file using SnakeGame."""
    if not output_file:
        output_file = input_file  # overwrite if no output specified

    with open(input_file, "r", encoding="utf-8") as f:
        tournament = json.load(f)

    bots = load_bots_from_folder()  # all UserBot objects
    bot_map = {bot.name: bot for bot in bots}

    # Play each match
    for group_name, group_data in tournament["groups"].items():
        for match in group_data["matches"]:
            team1_name, team2_name = list(match.keys())
            bot1 = bot_map.get(team1_name)
            bot2 = bot_map.get(team2_name)

            if not bot1 or not bot2:
                print(f"⚠️ Skipping match {team1_name} vs {team2_name} (bot not found)")
                continue

            print(f"\n🎮 Playing {bot1.name} vs {bot2.name}")
            game = SnakeGame(bot1.__class__, bot2.__class__, total_rounds=3, headless=headless)
            winner_name = game.run()  # Returns winner after all rounds

            # Assign scores (winner 1, loser 0)
            if winner_name == bot1.name:
                match[team1_name]["score"] = 1
                match[team2_name]["score"] = 0
            else:
                match[team1_name]["score"] = 0
                match[team2_name]["score"] = 1

    # Update standings after all matches
    tournament = update_standings(tournament)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(tournament, f, indent=4, ensure_ascii=False)
    print(f"\n✅ All matches played! Tournament updated and saved to {output_file}")




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tournament CLI tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Discover bots
    discover_parser = subparsers.add_parser("discover", help="Discover all available bots")
    discover_parser.add_argument("-o", "--output", type=str, default="bots.json",
                                 help="Output JSON file with discovered bots")

    # Generate tournament
    gen_parser = subparsers.add_parser("generate", help="Generate tournament tables")
    gen_parser.add_argument("-t", "--teams", nargs="+", help="Team IDs (optional, will use bots.json if omitted)")
    gen_parser.add_argument("-g", "--group-size", type=int, required=True, help="Number of teams per group")
    gen_parser.add_argument("-o", "--output", type=str, default="tournament.json", help="Output JSON file")


    # Update standings
    update_parser = subparsers.add_parser("update", help="Update tournament standings from match results JSON")
    update_parser.add_argument("-i", "--input", required=True, help="Input JSON file with match results")
    update_parser.add_argument("-o", "--output", type=str, default="", help="Output JSON file (default: overwrite input)")

    # Get top K
    top_parser = subparsers.add_parser("top", help="Get top K teams from a tournament JSON")
    top_parser.add_argument("-i", "--input", required=True, help="Input JSON file")
    top_parser.add_argument("-k", type=int, required=True, help="Number of top teams to return")

    # Run league
    league_parser = subparsers.add_parser("league", help="Run a league tournament with all discovered bots")
    league_parser.add_argument("-g", "--group-size", type=int, default=4, help="Number of teams per group")

    # Show leaderboard
    show_parser = subparsers.add_parser("show", help="Show full leaderboard from a tournament JSON")
    show_parser.add_argument("-i", "--input", required=True, help="Input JSON file")

    # Report / Finalize
    report_parser = subparsers.add_parser("report", help="Save final JSON and export leaderboard (CSV/Markdown)")
    report_parser.add_argument("-i", "--input", required=True, help="Input tournament JSON")
    report_parser.add_argument("-o", "--output", default="final.json", help="Output final JSON (default: final.json)")
    report_parser.add_argument("--csv", default="", help="Optional CSV output path")
    report_parser.add_argument("--md", default="", help="Optional Markdown output path")

    # Play all matches
    play_parser = subparsers.add_parser("play", help="Play all matches in a tournament JSON")
    play_parser.add_argument("-i", "--input", required=True, help="Input tournament JSON")
    play_parser.add_argument("-o", "--output", default="", help="Output tournament JSON after playing")
    play_parser.add_argument("--headless", action="store_true", help="Run games without GUI for faster execution")

    args = parser.parse_args()

    if args.command == "discover":
        cli_discover(args.output)

    elif args.command == "generate":
        teams = args.teams
        if not teams:
            if not os.path.exists("bots.json"):
                print("No teams specified and bots.json not found. Run discover first.")
                sys.exit(1)
            with open("bots.json", "r") as f:
                bots = json.load(f)
            teams = list(bots.keys())

        results = generate_tournament_tables(teams, args.group_size)
        with open(args.output, "w") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)
        print(f"Tournament generated and saved to {args.output}")

    elif args.command == "play":
        cli_play(args.input, args.output, args.headless)

    elif args.command == "show":
        cli_show(args.input)
        
    elif args.command == "report":
        cli_report(args.input, args.output, args.csv, args.md)

    elif args.command == "update":
        if args.output == "":
            args.output = args.input
        with open(args.input, "r") as f:
            data = json.load(f)
        updated = update_standings(data)
        with open(args.output, "w") as f:
            json.dump(updated, f, indent=4)
        print(f"Tournament standings updated and saved to {args.output}")

    elif args.command == "top":
        with open(args.input, "r") as f:
            data = json.load(f)
        top_teams = " ".join(k_best(args.k, data))
        print(f"Top {args.k} teams: {top_teams}")
        
    elif args.command == "league":
        bots = load_bots_from_folder()
        if not bots:
            print("❌ No bots found in bots folder")
            sys.exit(1)

        print(f"✅ Loaded {len(bots)} bots")
        # pairwise tournament
        for i in range(len(bots)):
            for j in range(i + 1, len(bots)):
                bot1, bot2 = bots[i], bots[j]
                print(f"\n🎮 Match: {bot1.name} vs {bot2.name}")
                from main import SnakeGame  # import pygame game loop
                game = SnakeGame(bot1.__class__, bot2.__class__)
                game.run()  # runs full tournament until game ends


