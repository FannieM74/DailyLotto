from sqlalchemy import create_engine, Column, Integer, String, Date, UniqueConstraint, text
from sqlalchemy.orm import declarative_base, sessionmaker
import os

DATABASE_URL = "sqlite:///./data/daily_lotto.db"
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
with engine.connect() as conn:
    conn.execute(text("PRAGMA journal_mode=WAL"))
    conn.execute(text("PRAGMA busy_timeout=5000"))
    conn.commit()
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)


class Draw(Base):
    __tablename__ = "draws"
    row_id = Column(Integer, primary_key=True, autoincrement=True)
    game = Column(String, nullable=False, default="daily_lotto")
    id = Column(Integer, nullable=False)
    draw_date = Column(Date, nullable=False, index=True)
    n1 = Column(Integer, nullable=False)
    n2 = Column(Integer, nullable=False)
    n3 = Column(Integer, nullable=False)
    n4 = Column(Integer, nullable=False)
    n5 = Column(Integer, nullable=False)
    n6 = Column(Integer, nullable=True)
    bonus = Column(Integer, nullable=True)
    powerball = Column(Integer, nullable=True)
    machine = Column(String, nullable=True)
    __table_args__ = (UniqueConstraint("game", "draw_date", name="uix_game_date"),)


class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True)
    game = Column(String, nullable=False, default="daily_lotto")
    draw_date = Column(Date, nullable=False, index=True)
    method = Column(String, nullable=False)
    n1 = Column(Integer, nullable=False)
    n2 = Column(Integer, nullable=False)
    n3 = Column(Integer, nullable=False)
    n4 = Column(Integer, nullable=False)
    n5 = Column(Integer, nullable=False)
    n6 = Column(Integer, nullable=True)
    bonus = Column(Integer, nullable=True)
    powerball = Column(Integer, nullable=True)
    matches = Column(Integer, nullable=True)
    __table_args__ = (UniqueConstraint("game", "draw_date", "method", name="uix_game_date_method"),)


def init_db():
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(bind=engine)


def migrate_v1():
    """Migrate existing data without game column to include game='daily_lotto'."""
    session = SessionLocal()
    try:
        from sqlalchemy import text
        session.execute(text("UPDATE draws SET game = 'daily_lotto' WHERE game IS NULL OR game = ''"))
        session.execute(text("UPDATE predictions SET game = 'daily_lotto' WHERE game IS NULL OR game = ''"))
        session.commit()
    except Exception as e:
        print(f"Migration note: {e}")
    finally:
        session.close()
