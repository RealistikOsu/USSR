# USSR Utilities

This is a small collection of utilities using the USSR codebase that helps with the operation of the
server. These utilities are all interacted through using a CLI. Here is a brief description of what
each individual utility does.

## PP System Tester
Tests the effects of a PP system change prior to applying it server-wide.
![Result Example](https://i.imgur.com/nkd09L5.png)

### Usage
```
python3.9 pptester.py [userid] [mode] [c_mode]
```
| Argument | Description |
| --- | --- |
| userid | The ID of the user to run the calculation test on within the ID |
| mode | The mode integer (0-3) for the mode for fetched scores. |
| c_mode | The custom mode integer (0-2) for the custom mode (Vanilla/Relax/Autopilot) for the fetched scores |

## Server Stats Recalc Tool
Recalculates the whole server's total PP, average accuracy and max combo. It also places unrestricted users onto
their respective global and country leaderboards.

### Usage
```
python3.9 stats_recalc.py
```

Tool takes no command line arguments.

## Replay Insert Tool
Submits a score from a replay file into the server.

### Usage
```
python3.9 replay_insert.py [replay_path]
```

| Argument | Description |
| --- | --- |
| replay_path | The path to the replay to be inserted RELATIVE TO THE ROOT USSR DIRECTORY. |

### Notes
- The user that the replay is inserted under is worked out using the username of the replay.
