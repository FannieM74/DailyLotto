from datetime import date, timedelta
from zoneinfo import ZoneInfo


def next_draw_date(game: str) -> date:
    cfg = GAMES[game]
    today = date.today()
    days = cfg["draw_days"]
    for offset in range(14):
        d = today + timedelta(days=offset)
        if d.weekday() in days:
            return d
    return today


GAMES = {
    "daily_lotto": {
        "label": "Daily Lotto",
        "short": "DL",
        "pick_count": 5,
        "max_number": 36,
        "has_bonus": False,
        "has_powerball": False,
        "csv_url": "https://www.africanlottery.net/download/sa_daily_lotto.csv",
        "results_url": "https://www.africanlottery.net/daily-lotto/results/",
        "draw_days": [0, 1, 2, 3, 4, 5, 6],
        "predict_time": {"hour": 5, "minute": 0},
        "predict_days": [0, 1, 2, 3, 4, 5, 6],
        "backfill_time": {"hour": 6, "minute": 0},
        "backfill_days": [0, 1, 2, 3, 4, 5, 6],
        "parse_csv": "daily_lotto",
        "draw_cols": 5,
        "date_format_csv": "%d.%m.%Y",
        "date_format_web": "%Y-%m-%d",
    },
    "lotto": {
        "label": "Lotto",
        "short": "L",
        "pick_count": 6,
        "max_number": 58,
        "has_bonus": True,
        "has_powerball": False,
        "csv_url": "https://www.africanlottery.net/download/sa_lotto.csv",
        "results_url": "https://www.africanlottery.net/lotto/results/",
        "draw_days": [2, 5],
        "predict_time": {"hour": 4, "minute": 0},
        "predict_days": [2, 5],
        "backfill_time": {"hour": 6, "minute": 0},
        "backfill_days": [3, 6],
        "parse_csv": "lotto",
        "draw_cols": 6,
        "date_format_csv": "%d.%m.%Y",
        "date_format_web": "%Y-%m-%d",
    },
    "lotto_plus": {
        "label": "Lotto Plus",
        "short": "LP",
        "pick_count": 6,
        "max_number": 58,
        "has_bonus": True,
        "has_powerball": False,
        "csv_url": "https://www.africanlottery.net/download/sa_lotto_plus_1.csv",
        "results_url": "https://www.africanlottery.net/lotto-plus/results/",
        "draw_days": [2, 5],
        "predict_time": {"hour": 4, "minute": 5},
        "predict_days": [2, 5],
        "backfill_time": {"hour": 6, "minute": 5},
        "backfill_days": [3, 6],
        "parse_csv": "lotto",
        "draw_cols": 6,
        "date_format_csv": "%d.%m.%Y",
        "date_format_web": "%Y-%m-%d",
    },
    "powerball": {
        "label": "PowerBall",
        "short": "PB",
        "pick_count": 5,
        "max_number": 50,
        "has_bonus": False,
        "has_powerball": True,
        "powerball_max": 20,
        "csv_url": "https://www.africanlottery.net/download/sa_powerball.csv",
        "results_url": "https://www.africanlottery.net/powerball/results/",
        "draw_days": [1, 4],
        "predict_time": {"hour": 5, "minute": 0},
        "predict_days": [1, 4],
        "backfill_time": {"hour": 6, "minute": 0},
        "backfill_days": [2, 5],
        "parse_csv": "powerball",
        "draw_cols": 5,
        "date_format_csv": "%d.%m.%Y",
        "date_format_web": "%Y-%m-%d",
    },
    "powerball_xtra": {
        "label": "PowerBall XTRA",
        "short": "PX",
        "pick_count": 5,
        "max_number": 50,
        "has_bonus": False,
        "has_powerball": True,
        "powerball_max": 20,
        "csv_url": "https://www.africanlottery.net/download/sa_powerball_xtra.csv",
        "results_url": "https://www.africanlottery.net/powerball-xtra/results/",
        "draw_days": [1, 4],
        "predict_time": {"hour": 5, "minute": 5},
        "predict_days": [1, 4],
        "backfill_time": {"hour": 6, "minute": 5},
        "backfill_days": [2, 5],
        "parse_csv": "powerball",
        "draw_cols": 5,
        "date_format_csv": "%d.%m.%Y",
        "date_format_web": "%Y-%m-%d",
    },
}

SAST = ZoneInfo("Africa/Johannesburg")
