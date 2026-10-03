# BurstCLI

A Windows terminal typing trainer designed to improve **burst typing speed** through strict accuracy, word-level records, and repeated speed challenges.

> **Vibecoded project:** BurstCLI was developed using AI-assisted tools and tested by the author.

## Features

* Word-by-word personal speed records
* Strict character-by-character accuracy
* Failed attempts reset immediately
* Backspace disabled
* Automatic progression between words
* Repeat challenges for breaking records multiple times
* Persistent JSON profiles
* Resume from the last completed word
* Continuous dataset looping
* Live WPM and typing feedback
* Arrow-key word navigation
* 500 WPM recognition ceiling
* Windows terminal UI with ANSI rendering
* Multiple independent word profiles
* Automatic lowercase conversion for loaded datasets

## Burst Speed Training

BurstCLI is built around **short, fast typing bursts** rather than long typing tests.

Each word becomes an individual speed challenge. To improve a recorded time, you must type the word perfectly and beat the existing record. **A space at the end of the word is required to submit the record.**

You can require multiple improvements with `--repeat`:

```bash
python burstcli.py --profile sample --repeat 4
```

With `--repeat 4`, the current word must be successfully improved **four times** before moving on. Failed or slower attempts do not count.

The four successful times are averaged and saved as the new record.

For words without an existing record, four successful attempts are simply averaged to create the initial record.

## 500 WPM Ceiling

BurstCLI uses a 500 WPM recognition ceiling to prevent extremely short words from producing unrealistic records.

The minimum recognized time is:

```text
characters × 0.024 seconds
```

Times faster than this threshold are normalized to the 500 WPM limit.

## Installation

```bash
git clone https://github.com/j-waweru/burstcli.git
cd burstcli
```

Requires **Python 3.10+** and currently uses only the Python standard library.

## Quick Start

BurstCLI includes `sample.words`, containing the **top 200 English words** as a ready-to-use sample dataset.

Create a profile:

```bash
python burstcli.py --load sample.words
```

Run it:

```bash
python burstcli.py --profile sample
```

Or require four successful speed improvements per word:

```bash
python burstcli.py --profile sample --repeat 4
```

List available profiles:

```bash
python burstcli.py --list
```

Datasets can contain words separated by spaces, commas, or newlines. Loaded words are automatically converted to lowercase.

## Controls

| Key         | Action                      |
| ----------- | --------------------------- |
| Characters  | Type the displayed word     |
| `Space`     | Submit the word             |
| `← → ↑ ↓`   | Navigate between words      |
| `Backspace` | Disabled; fails the attempt |
| `Ctrl+C`    | Exit                        |

## Profiles

Each dataset becomes a JSON profile containing the words, personal records, and current position.

Example:

```json
{
    "name": "sample",
    "dataset": "sample.words",
    "words": [
        "the",
        "be",
        "to"
    ],
    "records": {
        "the": null,
        "be": null,
        "to": null
    },
    "next_index": 0
}
```

Progress is saved automatically, allowing BurstCLI to resume where you left off.

## Project Goals

BurstCLI is intentionally small and focused on:

* Improving burst typing speed
* Building faster recognition of common words
* Strict accuracy
* Personal speed records
* Repeated speed improvement
* Fast feedback
* Simple persistent storage
* Terminal-first operation

## Current Limitations

* Primarily designed for Windows terminals
* No graphical interface
* No cloud synchronization
* No user accounts
* No multiplayer
* No analytics dashboard
* Records are keyed by word

## Coming Soon 

Support for linux terminals.

## License

No license has been selected yet.

---

**BurstCLI** — train faster bursts, one word at a time.
