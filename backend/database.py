from sqlalchemy import create_engine, Column, Integer, String, Date, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker
import os

DATABASE_URL = "sqlite:///./data/daily_lotto.db"
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)


class Draw(Base):
    __tablename__ = "draws"
    id = Column(Integer, primary_key=True, autoincrement=False)
    draw_date = Column(Date, unique=True, nullable=False, index=True)
    n1 = Column(Integer, nullable=False)
    n2 = Column(Integer, nullable=False)
    n3 = Column(Integer, nullable=False)
    n4 = Column(Integer, nullable=False)
    n5 = Column(Integer, nullable=False)
    machine = Column(String, nullable=True)


class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True)
    draw_date = Column(Date, nullable=False, index=True)
    method = Column(String, nullable=False)
    n1 = Column(Integer, nullable=False)
    n2 = Column(Integer, nullable=False)
    n3 = Column(Integer, nullable=False)
    n4 = Column(Integer, nullable=False)
    n5 = Column(Integer, nullable=False)
    matches = Column(Integer, nullable=True)
    __table_args__ = (UniqueConstraint("draw_date", "method", name="uix_draw_method"),)


def init_db():
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(bind=engine)
