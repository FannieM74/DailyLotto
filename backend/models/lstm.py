import os
import numpy as np
from database import SessionLocal, Draw
from games import GAMES
import threading

_training_lock = threading.Lock()

SEQ_LEN = 10
HIDDEN_SIZE = 64
LEARNING_RATE = 0.5
EPOCHS = 300
MOMENTUM = 0.9


def _get_nums(d, pick_count):
    nums = [d.n1, d.n2, d.n3, d.n4, d.n5]
    if pick_count > 5 and d.n6 is not None:
        nums.append(d.n6)
    return nums


def model_path(game):
    return os.path.join(
        os.path.dirname(__file__), "..", "data", f"lstm_{game}.npz"
    )


def softmax(x):
    e_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
    return e_x / np.sum(e_x, axis=-1, keepdims=True)


def relu(x):
    return np.maximum(0, x)


def relu_deriv(x):
    return (x > 0).astype(float)


def draws_to_sequences(game):
    cfg = GAMES[game]
    NUM_NUMBERS = cfg["max_number"]
    PICK = cfg["pick_count"]

    session = SessionLocal()
    draws = session.query(Draw).filter(Draw.game == game).order_by(Draw.draw_date).all()
    session.close()
    if len(draws) < SEQ_LEN + 1:
        return None, None
    nums_list = []
    for d in draws:
        nums_list.append(_get_nums(d, PICK))
    X, y = [], []
    for i in range(len(nums_list) - SEQ_LEN):
        seq = nums_list[i : i + SEQ_LEN]
        target = nums_list[i + SEQ_LEN]
        seq_oh = np.zeros((SEQ_LEN * NUM_NUMBERS,), dtype=np.float32)
        for t, nums in enumerate(seq):
            for n in nums:
                seq_oh[t * NUM_NUMBERS + n - 1] = 1.0
        target_oh = np.zeros(NUM_NUMBERS, dtype=np.float32)
        for n in target:
            target_oh[n - 1] += 1.0 / PICK
        X.append(seq_oh)
        y.append(target_oh)
    return np.array(X), np.array(y)


def init_weights(num_numbers):
    return {
        "W1": np.random.randn(SEQ_LEN * num_numbers, HIDDEN_SIZE).astype(np.float32) * 0.01,
        "b1": np.zeros((HIDDEN_SIZE,), dtype=np.float32),
        "W2": np.random.randn(HIDDEN_SIZE, num_numbers).astype(np.float32) * 0.01,
        "b2": np.zeros((num_numbers,), dtype=np.float32),
    }


def forward(X, params):
    z1 = X @ params["W1"] + params["b1"]
    a1 = relu(z1)
    z2 = a1 @ params["W2"] + params["b2"]
    a2 = softmax(z2)
    return a2, {"z1": z1, "a1": a1, "z2": z2}


def train_lstm(game, epochs=EPOCHS):
    if not _training_lock.acquire(blocking=False):
        print("Training already in progress, skipping")
        return True
    try:
        X, y = draws_to_sequences(game)
        if X is None:
            print("Not enough data to train")
            return False

        cfg = GAMES[game]
        NUM_NUMBERS = cfg["max_number"]

        params = init_weights(NUM_NUMBERS)
        n = X.shape[0]

        velocity = {k: np.zeros_like(v) for k, v in params.items()}

        for epoch in range(epochs):
            a2, cache = forward(X, params)
            loss = -np.mean(np.sum(y * np.log(a2 + 1e-8), axis=1))

            dz2 = a2 - y
            dW2 = cache["a1"].T @ dz2 / n + 1e-4 * params["W2"]
            db2 = np.mean(dz2, axis=0)
            da1 = dz2 @ params["W2"].T
            dz1 = da1 * relu_deriv(cache["z1"])
            dW1 = X.T @ dz1 / n + 1e-4 * params["W1"]
            db1 = np.mean(dz1, axis=0)

            grads = {"W2": dW2, "b2": db2, "W1": dW1, "b1": db1}
            for k in params:
                velocity[k] = MOMENTUM * velocity[k] + LEARNING_RATE * grads[k]
                params[k] -= velocity[k]

            if epoch < 20 or (epoch + 1) % 20 == 0:
                print(f"Epoch {epoch + 1}/{epochs}, Loss: {loss:.4f}")

        mp = model_path(game)
        os.makedirs(os.path.dirname(mp), exist_ok=True)
        np.savez(mp, **params)
        print(f"Model saved to {mp}")
        return True
    except Exception as e:
        print(f"Training failed: {e}")
        return False
    finally:
        _training_lock.release()


def load_model(game):
    mp = model_path(game)
    if os.path.exists(mp):
        data = np.load(mp)
        return {k: data[k] for k in data.files}
    return None


def predict_with_model(params, seq_oh):
    seq_flat = seq_oh.reshape(1, -1)
    a2, _ = forward(seq_flat, params)
    return a2[0]


def get_lstm_prediction(game):
    cfg = GAMES[game]
    N = cfg["max_number"]
    PICK = cfg["pick_count"]

    params = load_model(game)
    if params is None:
        return {"error": "No trained model available. Run train first."}

    session = SessionLocal()
    draws = session.query(Draw).filter(Draw.game == game).order_by(Draw.draw_date).all()
    session.close()

    if len(draws) < SEQ_LEN:
        return {"error": "Not enough draw data"}

    recent = draws[-SEQ_LEN:]
    seq_oh = np.zeros((SEQ_LEN, N), dtype=np.float32)
    for t, d in enumerate(recent):
        for n in _get_nums(d, PICK):
            seq_oh[t, n - 1] = 1.0

    probs = predict_with_model(params, seq_oh)
    top_indices = np.argsort(probs)[-PICK:][::-1]
    picks = [int(i) + 1 for i in sorted(top_indices)]
    top_probs = [float(probs[i]) for i in top_indices]

    return {
        "picks": picks,
        "probabilities": top_probs,
        "model_available": True,
    }
