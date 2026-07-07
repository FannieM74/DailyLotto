import httpx
from bs4 import BeautifulSoup
from datetime import datetime

CSV_URL = "https://www.africanlottery.net/download/sa_daily_lotto.csv"
RESULTS_URL = "https://www.africanlottery.net/daily-lotto/results/"


def download_csv() -> str:
    resp = httpx.get(CSV_URL, timeout=30)
    resp.raise_for_status()
    return resp.text


def scrape_latest_draws() -> list[dict]:
    resp = httpx.get(RESULTS_URL, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    rows = soup.select("table.tablep tr.trzwykly")
    draws = []
    for row in rows[:3]:
        cols = row.find_all("td")
        if len(cols) >= 3:
            draw_num = int(cols[0].text.strip())
            date_str = cols[1].text.strip()
            nums = [int(x.strip()) for x in cols[2].text.strip().split(",")]
            if len(nums) == 5 and date_str.count("-") == 2:
                draw_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                draws.append(
                    {
                        "id": draw_num,
                        "draw_date": draw_date,
                        "n1": nums[0],
                        "n2": nums[1],
                        "n3": nums[2],
                        "n4": nums[3],
                        "n5": nums[4],
                    }
                )
    return draws


def parse_csv(csv_text: str) -> list[dict]:
    draws = []
    for line in csv_text.strip().split("\n"):
        parts = line.strip().split(",")
        if len(parts) >= 7:
            draw_num = int(parts[0])
            date_str = parts[1]
            nums = [int(x) for x in parts[2:7]]
            machine = parts[7] if len(parts) > 7 else ""
            draw_date = datetime.strptime(date_str, "%d.%m.%Y").date()
            draws.append(
                {
                    "id": draw_num,
                    "draw_date": draw_date,
                    "n1": nums[0],
                    "n2": nums[1],
                    "n3": nums[2],
                    "n4": nums[3],
                    "n5": nums[4],
                    "machine": machine,
                }
            )
    return draws
