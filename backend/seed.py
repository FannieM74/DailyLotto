from database import SessionLocal, Draw, init_db
from scraper import download_csv, scrape_latest_draws, parse_csv


def seed_database():
    init_db()
    session = SessionLocal()

    print("Downloading CSV...")
    csv_text = download_csv()
    csv_draws = parse_csv(csv_text)
    print(f"Parsed {len(csv_draws)} draws from CSV")

    print("Scraping latest draws from webpage...")
    web_draws = scrape_latest_draws()
    print(f"Found {len(web_draws)} latest draws on webpage")

    all_draws = {d["id"]: d for d in csv_draws}
    for d in web_draws:
        all_draws[d["id"]] = d
    all_draws_list = sorted(all_draws.values(), key=lambda x: x["id"])

    inserted = 0
    for d in all_draws_list:
        existing = session.query(Draw).filter_by(draw_date=d["draw_date"]).first()
        if not existing:
            session.add(
                Draw(
                    id=d["id"],
                    draw_date=d["draw_date"],
                    n1=d["n1"],
                    n2=d["n2"],
                    n3=d["n3"],
                    n4=d["n4"],
                    n5=d["n5"],
                    machine=d.get("machine", ""),
                )
            )
            inserted += 1

    session.commit()
    total = session.query(Draw).count()
    print(f"Inserted {inserted} new draws. Total in DB: {total}")
    session.close()


if __name__ == "__main__":
    seed_database()
