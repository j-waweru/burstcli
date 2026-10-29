# BurstCLI

A Windows terminal typing trainer designed to improve **burst typing speed** through strict accuracy, word-level records, and repeated speed challenges.

> **Vibecoded project:** BurstCLI was developed using AI-assisted tools and tested by the author.

## Features

- Windows terminal UI with ANSI rendering
- Word-by-word personal speed records
- Persistent JSON profiles
- Live WPM and typing feedback
- Profile statistics with `--stats`
- Slowest-first word ordering after completing a full run
- Configurable successful attempts per word with `--repeat`

## Burst Speed Training

BurstCLI is built around **short, fast typing bursts** rather than long typing tests.

Each word becomes an individual speed challenge. To improve a recorded time, you must type the word perfectly and beat the existing record. **A space at the end of the word is required to submit the record.**

You can require multiple successful improvements with `--repeat`. With `--repeat 4`, the current word must be successfully improved **four times** before moving on. Failed or slower attempts do not count. The four successful times are averaged and saved as the new record. For words without an existing record, four successful attempts are averaged to create the initial record.

BurstCLI uses a **500 WPM recognition ceiling** to prevent extremely short words from producing unrealistic records. WPM is capped at 500, and records that exceed the ceiling are normalized to the equivalent minimum time.

## Installation

```bash
git clone https://github.com/j-waweru/burstcli.git
cd burstcli
```

Requires **Python 3.10+** and currently uses only the Python standard library.

BurstCLI includes a `samplewords` directory with ready-to-load datasets. To start, try `english200`.

## Usage

Create a profile from a dataset:

```bash
python burstcli.py --load samplewords/english200.words
```

Run a profile:

```bash
python burstcli.py --profile english200
```

Require four successful attempts per word:

```bash
python burstcli.py --profile english200 --repeat 4
```

List available profiles:

```bash
python burstcli.py --list
```

Show statistics for a profile:

```bash
python burstcli.py --stats english200
```

The statistics command reads the profile and prints a report directly in the terminal, including the number of recorded and unrecorded words, the number of words at the 500 WPM ceiling, the average WPM for recorded words below the ceiling, the 10 fastest non-maxed words, the 10 slowest recorded words, and unrecorded words. The average excludes unrecorded words and words at the ceiling because their exact speed cannot be determined.

Datasets can contain words separated by spaces, commas, or newlines. Loaded words are automatically converted to lowercase.

Each profile's progress and word records are saved automatically.


## Controls

| Key | Action |
| --- | --- |
| Characters | Type the displayed word |
| `Space` | Submit the word |
| `←` / `→` / `↑` / `↓` | Navigate between available words; forward navigation is limited to unlocked progress |
| `Backspace` | Disabled; a backspace attempt fails the current attempt |
| `Ctrl+C` | Return to the main menu when launched from the menu; otherwise interrupt the current run |

## Current Limitations

- Windows only
- No graphical interface
- No cloud synchronization
- No user accounts
- No multiplayer

## Coming Soon

- Rewrite in Rust
- Linux support
- Support for quotes and code

## License

No license has been selected yet.
