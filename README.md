# BurstCLI

A terminal-based typing trainer focused on **personal word-speed records, strict accuracy, and repeatable speed improvement**.

> **Vibecoded project:** BurstCLI was developed using AI-assisted/vibecoding workflows. The code, behavior, and design were iteratively developed and tested by the author.

## Features

* Terminal-based typing trainer for Windows
* Personal speed record for every word
* Records stored persistently in JSON profiles
* Strict character-by-character validation
* One incorrect character immediately fails the attempt
* Backspace is disabled
* Space submits the completed word
* Automatically resumes from the last completed word
* Dataset loops continuously
* Supports comma-, whitespace-, and newline-separated datasets
* Live typing feedback
* Live WPM calculation
* Progress bar
* ANSI terminal styling
* Success, mistake, and too-slow result screens
* 500 WPM recognition ceiling
* Automatic record normalization to the 500 WPM ceiling
* Multiple independent typing profiles

## How It Works

BurstCLI uses a simple progression system.

For each word:

1. The word is displayed.
2. The timer starts when the first character is typed.
3. Each character must match the target exactly.
4. A wrong character immediately fails the attempt.
5. Backspace is disabled.
6. Pressing `Space` submits the word.
7. The resulting time is compared with the previous record.
8. If the attempt beats the previous record, the new record is saved.
9. The trainer advances to the next word.
10. Progress is saved immediately.

On subsequent sessions, BurstCLI resumes from the next unfinished word.

## 500 WPM Ceiling

BurstCLI has a hard recognition ceiling of **500 WPM**.

The ceiling is not simply a display limit. It is part of the scoring system.

The minimum recognized time for a word is:

```text
time = characters × 0.024 seconds
```

Examples:

| Word length | 500 WPM threshold |
| ----------: | ----------------: |
|           2 |             48 ms |
|           3 |             72 ms |
|           4 |             96 ms |
|           5 |            120 ms |
|           6 |            144 ms |
|           7 |            168 ms |
|           8 |            192 ms |
|          10 |            240 ms |
|          12 |            288 ms |

If a word is typed faster than the threshold, its recorded time is normalized to the threshold and the word is marked **MAXED**.

Once a word is maxed, the user does not need to beat an increasingly impossible record. Typing at or faster than the 500 WPM threshold is sufficient to pass it.

## WPM Calculation

BurstCLI uses the standard five-character word convention:

```text
WPM = (characters / 5) / minutes
```

The calculated value is capped at 500 WPM.

Timing uses Python's high-resolution:

```python
time.perf_counter()
```

## Profiles

Each dataset can be converted into a persistent BurstCLI profile.

For example:

```text
mywords.txt
```

can become:

```text
mywords.json
```

A profile contains the dataset, records, and current position.

Example:

```json
{
    "name": "mywords",
    "dataset": "mywords.txt",
    "words": [
        "pointer",
        "memory",
        "buffer"
    ],
    "records": {
        "pointer": null,
        "memory": null,
        "buffer": null
    },
    "next_index": 0
}
```

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/burstcli.git
cd burstcli
```

BurstCLI currently uses Python's standard library, so there are no external Python packages required.

Python 3.10+ is recommended.

## Usage

### Create a profile

Create a text file containing your words:

```text
pointer
memory
buffer
process
thread
kernel
```

Then run:

```bash
python burstcli.py --load mywords.txt
```

This creates:

```text
mywords.json
```

### Run a profile

```bash
python burstcli.py --profile mywords
```

### List profiles

```bash
python burstcli.py --list
```

Example:

```text
BURSTCLI
PROFILES
────────────────────────────────────────────────────────────────

  1  programming
      Words   : 200
      Progress: 10/200
      File    : programming.json

  2  cybersecurity
      Words   : 150
      Progress: 37/150
      File    : cybersecurity.json

2 profile(s)
```

## Dataset Format

Datasets can use different separators.

### One word per line

```text
pointer
memory
buffer
register
process
```

### Space separated

```text
pointer memory buffer register process
```

### Comma separated

```text
pointer, memory, buffer, register, process
```

Mixed whitespace and commas are also supported.

## Controls

| Key         | Action                            |
| ----------- | --------------------------------- |
| Characters  | Type the target word              |
| `Space`     | Submit the word                   |
| `Backspace` | Disabled; causes a failed attempt |
| `Ctrl+C`    | Exit BurstCLI                     |

## UI

The interface uses ANSI terminal styling and a fixed-width dashboard.

It provides:

* Current word position
* Target word
* Live character feedback
* Current elapsed time
* Current WPM
* Personal record
* Record WPM
* MAXED status
* Dataset progress
* Attempt results

The interface is designed to remain fixed while typing rather than scrolling the terminal.

## Project Structure

The project is intentionally small.

```text
burstcli/
│
├── burstcli.py
├── README.md
│
├── mywords.txt
├── mywords.json
│
└── ...
```

The main application is currently contained in:

```text
burstcli.py
```

Profiles are stored separately as JSON files.

## Technical Details

BurstCLI currently uses only Python's standard library:

```python
json
math
os
re
sys
time
pathlib
msvcrt
```

### Windows Input

Windows raw keyboard input is handled using:

```python
msvcrt.getwch()
```

This allows BurstCLI to process individual key presses without requiring the user to press Enter.

### Terminal Rendering

The interface uses ANSI escape sequences for:

* Colors
* Cursor visibility
* Screen clearing
* Fixed dashboard rendering
* Box-drawing UI

Windows virtual terminal processing is enabled where supported.

## Design Goals

The project is intentionally focused on a small set of mechanics rather than becoming a general-purpose typing application.

The main goals are:

* Fast feedback
* Strict accuracy
* Persistent personal records
* Minimal controls
* Repeatable practice
* Terminal-first operation
* Simple data storage
* No external database
* No unnecessary dependencies

## Current Limitations

BurstCLI is currently designed primarily for **Windows terminals** because it uses `msvcrt` for keyboard input.

Other current limitations include:

* One profile corresponds to one dataset
* Records are keyed by word
* No graphical interface
* No multiplayer functionality
* No cloud synchronization
* No user accounts
* No statistical analytics dashboard
* No configurable difficulty system yet

## Why I Built It

BurstCLI was built as a small programming project around a simple idea:

> Turn individual words into personal speed challenges rather than treating typing speed as one overall score.

The project also serves as an experiment in building a useful CLI application with persistent state, real-time input handling, terminal rendering, and timing-sensitive logic.

## Development

This project was **vibecoded** using AI-assisted development.

The implementation was created through iterative prompting, code generation, debugging, testing, and refinement. The author reviewed and tested the resulting behavior and made decisions about the application's functionality, scoring rules, UI, and architecture.

The project is therefore intentionally transparent about its development process rather than presenting the code as entirely manually written.

## License

No license has been selected yet.

If you want others to freely use, modify, and redistribute the project, consider adding an open-source license such as MIT.

---

**BurstCLI** — terminal typing practice with persistent personal records.
