# Replay Prefix Adder
This is a simple utility made to fix a bug caused by the 19/6/22 rewrite where new replays
would me named incorrectly.

## Requirements
This migration has the same exact requirements as USSR itself.
- Python >=3.8
- A previously generated USSR config with correct paths set.

## Running the migrator
To run this migrator, just run the command
```sh
python3 main.py
```
replacing `python3` with your corresponding python executable.

## Important note!
Do not move the main.py from its directory! This is because the migration makes a few assumptions based on the
current working directory, meaning your file structure may not match up if its moved.
