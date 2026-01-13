import pandas as pd
import numpy as np
import pickle

from sklearn.neighbors import KNeighborsRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

# ===== ŚCIEŻKI =====
TRAIN_CSV = "../datasets/train_dataset_scaled.csv"
TEST_CSV = "../datasets/test_dataset_scaled.csv"
MODEL_OUT = "../models/knn_model.pkl"

# ===== PARAMETRY MODELU =====
K = 15
WEIGHTS = "distance"  # bardzo ważne dla KNN
METRIC = "euclidean"

# ===== WCZYTANIE DANYCH =====
print("Loading datasets...")

train_df = pd.read_csv(TRAIN_CSV)
test_df = pd.read_csv(TEST_CSV)

X_train = train_df.drop(columns=["y"]).values
y_train = train_df["y"].values

X_test = test_df.drop(columns=["y"]).values
y_test = test_df["y"].values

print(f"Train samples: {X_train.shape}")
print(f"Test samples:  {X_test.shape}")

# ===== MODEL =====
print("Training KNN...")

knn = KNeighborsRegressor(
    n_neighbors=K,
    weights=WEIGHTS,
    metric=METRIC,
    n_jobs=-1,
)

knn.fit(X_train, y_train)

# ===== TEST =====
print("Evaluating on test set...")

y_pred = knn.predict(X_test)

mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))

print(f"MAE  = {mae:.6f}")
print(f"RMSE = {rmse:.6f}")

# ===== ZAPIS MODELU =====
print("Saving model...")

with open(MODEL_OUT, "wb") as f:
    pickle.dump(knn, f)

print(f"Model saved to {MODEL_OUT}")
