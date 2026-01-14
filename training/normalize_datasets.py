import pandas as pd
from sklearn.preprocessing import StandardScaler
import os

# ========== ŚCIEŻKI ==========
TRAIN_PATH = "../datasets/train_dataset.csv"
TEST_PATH = "../datasets/test_dataset.csv"

OUT_TRAIN_PATH = "../datasets/train_dataset_scaled.csv"
OUT_TEST_PATH = "../datasets/test_dataset_scaled.csv"
# =============================

# 1️⃣ Wczytaj dane
train_df = pd.read_csv(TRAIN_PATH)
test_df = pd.read_csv(TEST_PATH)

# 2️⃣ Usuń kolumny niemodelowe
DROP_COLS = ["node", "scenario"]

train_df = train_df.drop(columns=DROP_COLS)
test_df = test_df.drop(columns=DROP_COLS)

# 3️⃣ Oddziel X i y
X_train = train_df.drop(columns=["y"])
y_train = train_df["y"]

X_test = test_df.drop(columns=["y"])
y_test = test_df["y"]

# 4️⃣ Normalizacja (FIT tylko na TRAIN)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# 5️⃣ Złóż z powrotem DataFrame
train_scaled_df = pd.DataFrame(X_train_scaled, columns=X_train.columns)
train_scaled_df["y"] = y_train.values

test_scaled_df = pd.DataFrame(X_test_scaled, columns=X_test.columns)
test_scaled_df["y"] = y_test.values

# 6️⃣ Zapisz
train_scaled_df.to_csv(OUT_TRAIN_PATH, index=False)
test_scaled_df.to_csv(OUT_TEST_PATH, index=False)

print("✅ Normalizacja zakończona")
print(f"TRAIN → {OUT_TRAIN_PATH}")
print(f"TEST  → {OUT_TEST_PATH}")
print(f"TRAIN samples: {len(train_scaled_df)}")
print(f"TEST samples: {len(test_scaled_df)}")
