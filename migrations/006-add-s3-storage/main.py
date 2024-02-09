from __future__ import annotations

import glob
import os

for folder in ("replays_relax", "replays_ap"):
    for path in glob.glob(f"../../.data/{folder}"):
        print(f"Moving {path} to .data/replays")
        file = os.path.basename(path)
        os.rename(path, f"../../.data/replays/{file}")
