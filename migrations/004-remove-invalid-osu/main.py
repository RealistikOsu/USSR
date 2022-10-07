import glob
import os

for path in glob.glob("../../.data/maps/*.osu"):
    with open(path, "rb") as f:
        if b"osu file format" not in f.read():
            print(f"Removing invalid osu file: {path}")
            os.remove(path)
