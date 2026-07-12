from database import SessionLocal, Draw, init_db
from scraper import download_csv, scrape_latest_draws, parse_csv


def seed_database(game: str = "daily_lotto"):
    init_db()
    session = SessionLocal()

    print(f"[{game}] Downloading CSV...")
    try:
        csv_text = download_csv(game)
        csv_draws = parse_csv(game, csv_text)
        print(f"[{game}] Parsed {len(csv_draws)} draws from CSV")
    except Exception as e:
        print(f"[{game}] CSV download failed: {e}")
        csv_draws = []

    print(f"[{game}] Scraping latest draws...")
    try:
        web_draws = scrape_latest_draws(game)
        print(f"[{game}] Found {len(web_draws)} latest draws on webpage")
    except Exception as e:
        print(f"[{game}] Web scrape failed: {e}")
        web_draws = []

    all_draws = {d["id"]: d for d in csv_draws}
    for d in web_draws:
        all_draws[d["id"]] = d
    all_draws_list = sorted(all_draws.values(), key=lambda x: x["id"])

    inserted = 0
    for d in all_draws_list:
        existing = session.query(Draw).filter_by(game=game, draw_date=d["draw_date"]).first()
        if not existing:
            session.add(Draw(
                game=game,
                id=d["id"],
                draw_date=d["draw_date"],
                n1=d["n1"], n2=d["n2"], n3=d["n3"], n4=d["n4"], n5=d["n5"],
                n6=d.get("n6"), bonus=d.get("bonus"), powerball=d.get("powerball"),
            ))
            inserted += 1

    session.commit()
    total = session.query(Draw).filter_by(game=game).count()
    print(f"[{game}] Inserted {inserted} new draws. Total in DB: {total}")
    session.close()


if __name__ == "__main__":
    import sys
    game = sys.argv[1] if len(sys.argv) > 1 else "daily_lotto"
    seed_database(game)
