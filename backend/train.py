from models.lstm import train_lstm
from seed import seed_database


def retrain():
    print("Seeding latest data...")
    seed_database()
    print("Training LSTM model...")
    train_lstm(epochs=50)
    print("Retrain complete")


if __name__ == "__main__":
    retrain()
