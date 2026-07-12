import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from games import GAMES


def download_csv(game: str) -> str:
    cfg = GAMES[game]
    resp = httpx.get(cfg["csv_url"], timeout=30)
    resp.raise_for_status()
    return resp.text


def scrape_latest_draws(game: str) -> list[dict]:
    cfg = GAMES[game]
    resp = httpx.get(cfg["results_url"], timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    rows = soup.select("table.tablep tr.trzwykly")
    draws = []
    for row in rows[:3]:
        cols = row.find_all("td")
        if len(cols) < 3:
            continue
        draw_num = int(cols[0].text.strip())
        date_str = cols[1].text.strip()
        raw = cols[2].text.strip().replace(" +", ",")
        nums = [int(x.strip()) for x in raw.replace(" ,", ",").split(",") if x.strip()]
        if cfg["has_bonus"] and len(nums) >= cfg["pick_count"] + 1:
            main = nums[: cfg["pick_count"]]
            bonus = nums[cfg["pick_count"]]
        elif cfg["has_powerball"] and len(nums) >= cfg["pick_count"] + 1:
            main = nums[: cfg["pick_count"]]
            powerball = nums[cfg["pick_count"]]
        else:
            main = nums[: cfg["pick_count"]]
            bonus = None
            powerball = None
        if len(main) != cfg["pick_count"] or date_str.count("-") != 2:
            continue
        draw_date = datetime.strptime(date_str, cfg["date_format_web"]).date()
        entry = {
            "id": draw_num,
            "draw_date": draw_date,
            "n1": main[0], "n2": main[1], "n3": main[2], "n4": main[3], "n5": main[4],
            "n6": main[5] if cfg["pick_count"] > 5 else None,
            "bonus": bonus if cfg.get("has_bonus") else None,
            "powerball": powerball if cfg.get("has_powerball") else None,
        }
        draws.append(entry)
    return draws


def parse_csv(game: str, csv_text: str) -> list[dict]:
    cfg = GAMES[game]
    draws = []
    for line in csv_text.strip().split("\n"):
        parts = [p.strip() for p in line.strip().split(",")]
        if len(parts) < cfg["pick_count"] + 2:
            continue
        try:
            draw_num = int(parts[0])
            date_str = parts[1]
            nums = [int(x) for x in parts[2 : 2 + cfg["pick_count"]]]
            bonus_val = None
            powerball_val = None
            idx = 2 + cfg["pick_count"]
            if cfg.get("has_bonus") and idx < len(parts):
                bonus_val = int(parts[idx])
                idx += 1
            elif cfg.get("has_powerball") and idx < len(parts):
                powerball_val = int(parts[idx])
                idx += 1
            draw_date = datetime.strptime(date_str, cfg["date_format_csv"]).date()
        except (ValueError, IndexError):
            continue
        entry = {
            "id": draw_num,
            "draw_date": draw_date,
            "n1": nums[0], "n2": nums[1], "n3": nums[2],
            "n4": nums[3], "n5": nums[4],
            "n6": nums[5] if cfg["pick_count"] > 5 else None,
            "bonus": bonus_val,
            "powerball": powerball_val,
        }
        draws.append(entry)
    return draws
