import os
import pandas as pd

# ================== PARAMETRY ==================

SNAPSHOTS_DIR = "../snapshots"
OUTPUT_DIR = "../datasets"

WINDOW_SIZE = 3  # sliding window length
PREDICT_AHEAD = 1  # +1 snapshot (np. +5 czasu)

FEATURE_COLS = [
    "mean_occupancy",
    "max_occupancy",
    "min_largest_free_block",
    "mean_fragmentation",
    "max_fragmentation",
]

LABEL_COL = "max_occupancy"

TRAIN_SUFFIXES = {"_0", "_1", "_2"}
TEST_SUFFIXES = {"_3", "_4"}

# ===============================================

os.makedirs(OUTPUT_DIR, exist_ok=True)

train_rows = []
test_rows = []

train_columns = None

# ------------------------------------------------


def is_train_file(filename: str) -> bool:
    return any(s in filename for s in TRAIN_SUFFIXES)


def is_test_file(filename: str) -> bool:
    return any(s in filename for s in TEST_SUFFIXES)


# ------------------------------------------------

for filename in os.listdir(SNAPSHOTS_DIR):
    if not filename.endswith(".csv"):
        continue

    file_path = os.path.join(SNAPSHOTS_DIR, filename)

    if is_train_file(filename):
        target_rows = train_rows
    elif is_test_file(filename):
        target_rows = test_rows
    else:
        print(f"⚠️ Pomijam plik (nieznany suffix): {filename}")
        continue

    print(f"📂 Przetwarzam: {filename}")

    df = pd.read_csv(file_path)

    # --- dla każdego węzła osobno ---
    for node_id in df["node"].unique():
        node_df = df[df["node"] == node_id].sort_values("time").reset_index(drop=True)

        if len(node_df) < WINDOW_SIZE + PREDICT_AHEAD:
            continue

        for i in range(WINDOW_SIZE - 1, len(node_df) - PREDICT_AHEAD):
            window = node_df.iloc[i - WINDOW_SIZE + 1 : i + 1]
            future = node_df.iloc[i + PREDICT_AHEAD]

            x = []
            for _, row in window.iterrows():
                for col in FEATURE_COLS:
                    x.append(row[col])

            y = future[LABEL_COL]

            row_data = {
                "scenario": filename,
                "node": node_id,
                "y": y,
            }

            # nazwy kolumn X
            col_idx = 0
            for w in range(WINDOW_SIZE):
                for col in FEATURE_COLS:
                    row_data[f"x{w}_{col}"] = x[col_idx]
                    col_idx += 1

            target_rows.append(row_data)

            if train_columns is None:
                train_columns = list(row_data.keys())

# ------------------------------------------------

train_df = pd.DataFrame(train_rows)
test_df = pd.DataFrame(test_rows)

train_df.to_csv(os.path.join(OUTPUT_DIR, "train_dataset.csv"), index=False)
test_df.to_csv(os.path.join(OUTPUT_DIR, "test_dataset.csv"), index=False)

print("✅ Gotowe")
print(f"TRAIN samples: {len(train_df)}")
print(f"TEST samples: {len(test_df)}")
