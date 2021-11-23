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
