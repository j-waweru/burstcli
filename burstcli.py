import json
import math
import os
import re
import sys
import time
from pathlib import Path
import msvcrt


# ============================================================
# Configuration
# ============================================================

MAX_WPM = 500.0
SECONDS_PER_CHARACTER_AT_MAX_WPM = 60 / (5 * MAX_WPM)
EPSILON = 1e-9

PROFILE_EXTENSION = ".json"

UI_WIDTH = 64
INNER_WIDTH = UI_WIDTH - 2
PROGRESS_WIDTH = 48



# ============================================================
# ANSI / Terminal styling
# ============================================================

class Style:
    RESET = "\033[0m"

    BOLD = "\033[1m"
    DIM = "\033[2m"

    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"


ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def visible_len(text):
    return len(ANSI_RE.sub("", text))


def styled(text, color="", bold=False, dim=False):
    parts = []

    if color:
        parts.append(color)

    if bold:
        parts.append(Style.BOLD)

    if dim:
        parts.append(Style.DIM)

    parts.append(text)
    parts.append(Style.RESET)

    return "".join(parts)


def enable_ansi():
    if os.name != "nt":
        return

    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint32()

        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(
                handle,
                mode.value | 0x0004
            )

    except Exception:
        pass


# ============================================================
# Terminal control
# ============================================================

def clear_screen():
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def hide_cursor():
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()


def show_cursor():
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()


def move_cursor_home():
    sys.stdout.write("\033[H")
    sys.stdout.flush()


def read_key():
    return msvcrt.getwch()


def wait_for_key():
    msvcrt.getwch()


def read_special_key():
    """
    Return:
        ("left" | "right" | "up" | "down" | "other", raw)

    Windows arrow keys arrive as an extended-key prefix followed
    by a second character.
    """
    key = read_key()

    if key in ("\x00", "\xe0"):
        code = read_key()

        mapping = {
            "K": "left",
            "M": "right",
            "H": "up",
            "P": "down",
        }

        return mapping.get(code, "other"), code

    return None, key


# ============================================================
# Fixed-width text helpers
# ============================================================

def pad_visible(text, width, align="left"):
    current_length = visible_len(text)

    if current_length >= width:
        if current_length > width:
            plain = ANSI_RE.sub("", text)
            return plain[:width]

        return text

    padding = width - current_length

    if align == "right":
        return " " * padding + text

    if align == "center":
        left = padding // 2
        right = padding - left
        return " " * left + text + " " * right

    return text + " " * padding


def centered_text(text, width=INNER_WIDTH):
    return pad_visible(text, width, "center")


# ============================================================
# Panel UI
# ============================================================

BORDER_TOP = "╭" + "─" * (UI_WIDTH - 2) + "╮"
BORDER_BOTTOM = "╰" + "─" * (UI_WIDTH - 2) + "╯"
BORDER_SEPARATOR = "├" + "─" * (UI_WIDTH - 2) + "┤"


def panel_line(content=""):
    content = pad_visible(content, INNER_WIDTH, "left")
    return "│" + content + "│"


def print_panel(lines):
    print(BORDER_TOP)

    for line in lines:
        print(panel_line(line))

    print(BORDER_BOTTOM)


# ============================================================
# Profile paths
# ============================================================

def profile_path(profile_name):
    return Path(f"{profile_name}{PROFILE_EXTENSION}")


# ============================================================
# Dataset
# ============================================================

def load_dataset_file(path):
    """
    Load comma, whitespace, or newline separated words.

    New profiles normalize every word to lowercase.
    """
    text = path.read_text(encoding="utf-8")
    text = text.replace(",", " ")

    words = [word.lower() for word in text.split()]

    if not words:
        raise ValueError("Dataset contains no words.")

    return words


# ============================================================
# Profile creation
# ============================================================

def create_profile_from_dataset(dataset_path):
    dataset_path = Path(dataset_path)

    if not dataset_path.exists():
        print(
            styled(
                f"Dataset not found: {dataset_path}",
                Style.BRIGHT_RED
            )
        )
        return False

    try:
        words = load_dataset_file(dataset_path)

    except (OSError, ValueError) as error:
        print(
            styled(
                f"Error loading dataset: {error}",
                Style.BRIGHT_RED
            )
        )
        return False

    profile_name = dataset_path.stem
    output_path = profile_path(profile_name)

    if output_path.exists():
        print(
            styled(
                f"Profile already exists: {output_path}",
                Style.BRIGHT_YELLOW
            )
        )

        print()

        answer = input("Overwrite it? [y/N]: ").strip().lower()

        if answer != "y":
            print("Profile not created.")
            return False

    records = {}

    for word in words:
        records[word] = None

    profile = {
        "name": profile_name,
        "dataset": dataset_path.name,
        "words": words,
        "records": records,
        "next_index": 0
    }

    try:
        output_path.write_text(
            json.dumps(profile, indent=4),
            encoding="utf-8"
        )

    except OSError as error:
        print(
            styled(
                f"Could not create profile: {error}",
                Style.BRIGHT_RED
            )
        )
        return False

    print()

    print(
        styled(
            "PROFILE CREATED",
            Style.BRIGHT_GREEN,
            bold=True
        )
    )

    print()
    print(
        f"  Profile : "
        f"{styled(output_path.name, Style.BRIGHT_CYAN)}"
    )
    print(
        f"  Words   : "
        f"{styled(str(len(words)), Style.BRIGHT_WHITE)}"
    )

    print()
    print("Run it with:")
    print(
        styled(
            f"  burstcli --profile {profile_name}",
            Style.BRIGHT_CYAN,
            bold=True
        )
    )

    return True


# ============================================================
# Profile loading
# ============================================================

def load_profile(profile_name):
    path = profile_path(profile_name)

    if not path.exists():
        print(
            styled(
                f"Profile not found: {path}",
                Style.BRIGHT_RED
            )
        )
        print()
        print(
            "Use "
            + styled("--list", Style.BRIGHT_CYAN)
            + " to see available profiles."
        )
        return None

    try:
        profile = json.loads(
            path.read_text(encoding="utf-8")
        )

    except (OSError, json.JSONDecodeError) as error:
        print(
            styled(
                f"Could not load profile: {error}",
                Style.BRIGHT_RED
            )
        )
        return None

    if not isinstance(profile, dict):
        print(styled("Invalid profile format.", Style.BRIGHT_RED))
        return None

    if "words" not in profile:
        print(
            styled(
                "Profile does not contain a word list.",
                Style.BRIGHT_RED
            )
        )
        return None

    if "records" not in profile:
        profile["records"] = {}

    if "next_index" not in profile:
        profile["next_index"] = 0

    words = profile["words"]

    if not isinstance(words, list) or not words:
        print(
            styled(
                "Profile contains no words.",
                Style.BRIGHT_RED
            )
        )
        return None

    # Normalize old profiles too. This means profiles created before
    # lowercase-on-load was added continue to work consistently.
    normalized_words = [str(word).lower() for word in words]

    old_records = profile["records"]
    normalized_records = {}

    for old_word, record in old_records.items():
        normalized_records[str(old_word).lower()] = record

    profile["words"] = normalized_words
    profile["records"] = normalized_records

    if not isinstance(profile["next_index"], int):
        profile["next_index"] = 0

    profile["next_index"] %= len(normalized_words)

    for word in normalized_words:
        if word not in profile["records"]:
            profile["records"][word] = None

    normalize_profile_records(profile)

    return profile


def save_profile(profile):
    path = profile_path(profile["name"])
    temp_path = path.with_suffix(".tmp")

    temp_path.write_text(
        json.dumps(profile, indent=4),
        encoding="utf-8"
    )

    temp_path.replace(path)


# ============================================================
# Profile listing
# ============================================================

def list_profiles():
    profiles = sorted(Path(".").glob("*.json"))
    valid_profiles = []

    for path in profiles:
        try:
            profile = json.loads(
                path.read_text(encoding="utf-8")
            )

        except (OSError, json.JSONDecodeError):
            continue

        if not isinstance(profile, dict):
            continue

        if "words" not in profile or "records" not in profile:
            continue

        valid_profiles.append((path, profile))

    clear_screen()

    print(
        styled(
            "BURSTCLI",
            Style.BRIGHT_CYAN,
            bold=True
        )
    )

    print(
        styled(
            "PROFILES",
            Style.WHITE,
            bold=True
        )
    )

    print(styled("─" * 64, Style.DIM))
    print()

    if not valid_profiles:
        print(
            styled(
                "No profiles found.",
                Style.YELLOW
            )
        )

        print()
        print("Create one with:")
        print(
            styled(
                "  burstcli --load mywords.txt",
                Style.BRIGHT_CYAN
            )
        )
        return

    for index, (path, profile) in enumerate(
        valid_profiles,
        start=1
    ):
        name = profile.get("name", path.stem)
        words = profile.get("words", [])
        next_index = profile.get("next_index", 0)

        print(
            f"  {styled(str(index), Style.DIM)}  "
            f"{styled(name, Style.BRIGHT_WHITE, bold=True)}"
        )

        print(f"      Words   : {len(words)}")
        print(
            f"      Progress: "
            f"{next_index + 1}/{len(words)}"
        )
        print(f"      File    : {path.name}")
        print()

    print(
        styled(
            f"{len(valid_profiles)} profile(s)",
            Style.DIM
        )
    )


# ============================================================
# Timing
# ============================================================

def max_wpm_time(word):
    return len(word) * SECONDS_PER_CHARACTER_AT_MAX_WPM


def effective_time(word, actual_seconds):
    return max(actual_seconds, max_wpm_time(word))


def calculate_wpm(word, seconds):
    if seconds <= 0:
        return MAX_WPM

    minutes = seconds / 60
    wpm = (len(word) / 5) / minutes

    return min(wpm, MAX_WPM)


def normalize_record(word, seconds):
    return max(
        float(seconds),
        max_wpm_time(word)
    )


def normalize_profile_records(profile):
    records = profile["records"]

    for word in profile["words"]:
        if word not in records:
            records[word] = None
            continue

        record = records[word]

        if record is None:
            continue

        try:
            records[word] = normalize_record(
                word,
                float(record)
            )

        except (TypeError, ValueError):
            records[word] = None


def is_maxed(word, record):
    if record is None:
        return False

    threshold = max_wpm_time(word)

    return math.isclose(
        float(record),
        threshold,
        rel_tol=0,
        abs_tol=EPSILON
    )


# ============================================================
# Formatting
# ============================================================

def format_ms(seconds):
    return f"{seconds * 1000:.1f} ms"


def format_wpm(word, seconds):
    return f"{calculate_wpm(word, seconds):.1f} WPM"


def progress_bar(current, total, width=PROGRESS_WIDTH):
    if total <= 0:
        return ""

    ratio = current / total
    ratio = max(0.0, min(ratio, 1.0))

    filled = int(ratio * width)
    filled = min(filled, width)

    empty = width - filled

    return (
        styled(
            "█" * filled,
            Style.BRIGHT_CYAN
        )
        +
        styled(
            "░" * empty,
            Style.DIM
        )
    )


# ============================================================
# Word display
# ============================================================

def render_word_progress(word, typed, error=False):
    """
    Correct characters are green.
    Current character is yellow.
    Remaining characters are dim.
    On error, the complete target is red.
    """
    if error:
        return styled(
            word,
            Style.BRIGHT_RED,
            bold=True
        )

    output = ""
    typed_length = len(typed)

    for index, character in enumerate(word):
        if index < typed_length:
            output += styled(
                character,
                Style.BRIGHT_GREEN,
                bold=True
            )

        elif index == typed_length:
            output += styled(
                character,
                Style.BRIGHT_YELLOW,
                bold=True
            )

        else:
            output += styled(
                character,
                Style.DIM
            )

    return output


# ============================================================
# Live typing UI
# ============================================================

def render_typing_screen(
    profile,
    word,
    word_number,
    total_words,
    typed,
    elapsed,
    previous_record,
    repeat_required=1,
    repeat_completed=0,
    navigation_message=""
):
    clear_screen()

    header_left = styled(
        "BURSTCLI",
        Style.BRIGHT_CYAN,
        bold=True
    )

    header_right = styled(
        f"{word_number}/{total_words}",
        Style.BRIGHT_WHITE,
        bold=True
    )

    header_space = (
        INNER_WIDTH
        - visible_len(header_left)
        - visible_len(header_right)
    )

    header_content = (
        header_left
        + " " * max(1, header_space)
        + header_right
    )

    print(panel_line(header_content))

    print(
        panel_line(
            styled(
                profile["name"],
                Style.DIM
            )
        )
    )

    print(BORDER_SEPARATOR)

    print(panel_line())

    target_display = styled(
        word,
        Style.BRIGHT_WHITE,
        bold=True
    )

    print(panel_line(centered_text(target_display)))
    print(panel_line())

    typed_display = render_word_progress(word, typed)
    print(panel_line(centered_text(typed_display)))
    print(panel_line())

    if elapsed is not None:
        recognized_time = effective_time(word, elapsed)
        current_wpm = calculate_wpm(word, recognized_time)

        stats = (
            f"{format_ms(recognized_time)}"
            f"  •  "
            f"{current_wpm:.1f} WPM"
        )

        print(
            panel_line(
                centered_text(
                    styled(
                        stats,
                        Style.BRIGHT_CYAN,
                        bold=True
                    )
                )
            )
        )

    else:
        print(
            panel_line(
                centered_text(
                    styled(
                        "READY",
                        Style.DIM,
                        bold=True
                    )
                )
            )
        )

    print(panel_line())

    if previous_record is None:
        record_text = (
            "Record: "
            + styled("--", Style.DIM)
        )

    elif is_maxed(word, previous_record):
        record_text = (
            "Record: "
            + styled(
                format_ms(previous_record),
                Style.BRIGHT_GREEN,
                bold=True
            )
            + "  "
            + styled(
                "MAXED",
                Style.BRIGHT_GREEN,
                bold=True
            )
        )

    else:
        record_text = (
            "Record: "
            + styled(
                format_ms(previous_record),
                Style.BRIGHT_WHITE,
                bold=True
            )
            + "  "
            + styled(
                format_wpm(word, previous_record),
                Style.BRIGHT_WHITE
            )
        )

    print(panel_line(centered_text(record_text)))
    print(panel_line())

    if repeat_required > 1:
        repeat_text = (
            f"Improvement set: "
            f"{repeat_completed}/{repeat_required}"
        )

        print(
            panel_line(
                centered_text(
                    styled(
                        repeat_text,
                        Style.BRIGHT_YELLOW,
                        bold=True
                    )
                )
            )
        )

        print(panel_line())

    bar = progress_bar(word_number, total_words)
    print(panel_line(centered_text(bar)))
    print(panel_line())

    if navigation_message:
        print(
            panel_line(
                centered_text(
                    styled(
                        navigation_message,
                        Style.BRIGHT_CYAN
                    )
                )
            )
        )
    else:
        print(
            panel_line(
                centered_text(
                    styled(
                        "← →  navigate words",
                        Style.DIM
                    )
                )
            )
        )

    print(
        panel_line(
            centered_text(
                styled(
                    "Type → SPACE to submit",
                    Style.DIM
                )
            )
        )
    )

    print(
        panel_line(
            centered_text(
                styled(
                    "Backspace disabled",
                    Style.DIM
                )
            )
        )
    )

    print(BORDER_BOTTOM)
    sys.stdout.flush()


# ============================================================
# Word navigation
# ============================================================

def move_word(profile, direction):
    total_words = len(profile["words"])

    if direction == "next":
        profile["next_index"] = (
            profile["next_index"] + 1
        ) % total_words

    elif direction == "previous":
        profile["next_index"] = (
            profile["next_index"] - 1
        ) % total_words

    save_profile(profile)


# ============================================================
# Word attempt
# ============================================================

def attempt_word(
    profile,
    word,
    word_number,
    total_words,
    previous_record,
    repeat_required,
    repeat_completed
):
    typed = ""
    start_time = None

    render_typing_screen(
        profile,
        word,
        word_number,
        total_words,
        typed,
        None,
        previous_record,
        repeat_required,
        repeat_completed
    )

    while True:
        key = read_key()

        if key == "\x03":
            raise KeyboardInterrupt

        # Arrow keys can navigate only before typing has started.
        if key in ("\x00", "\xe0"):
            code = read_key()

            mapping = {
                "K": "left",
                "M": "right",
                "H": "up",
                "P": "down",
            }

            direction = mapping.get(code)

            if direction in ("left", "up"):
                if start_time is None and not typed:
                    return {
                        "status": "navigate",
                        "direction": "previous"
                    }

            elif direction in ("right", "down"):
                if start_time is None and not typed:
                    return {
                        "status": "navigate",
                        "direction": "next"
                    }

            # Any other special key is treated as an immediate mistake.
            if start_time is not None or typed:
                return {
                    "status": "mistake",
                    "actual_time": None,
                    "effective_time": None
                }

            continue

        # Backspace is disabled and immediately fails the attempt.
        if key == "\x08":
            return {
                "status": "mistake",
                "actual_time": None,
                "effective_time": None
            }

        # Space submits.
        if key == " ":
            if start_time is None:
                return {
                    "status": "mistake",
                    "actual_time": None,
                    "effective_time": None
                }

            actual_time = (
                time.perf_counter() - start_time
            )

            if typed != word:
                return {
                    "status": "mistake",
                    "actual_time": actual_time,
                    "effective_time": effective_time(
                        word,
                        actual_time
                    )
                }

            recognized_time = effective_time(
                word,
                actual_time
            )

            threshold = max_wpm_time(word)

            # No existing record:
            # every perfect attempt is a qualifying attempt.
            if previous_record is None:
                return {
                    "status": "success",
                    "actual_time": actual_time,
                    "effective_time": recognized_time
                }

            # Existing maxed record:
            # at/below the 500 WPM threshold qualifies.
            if is_maxed(word, previous_record):
                if actual_time <= threshold + EPSILON:
                    return {
                        "status": "success",
                        "actual_time": actual_time,
                        "effective_time": threshold
                    }

                return {
                    "status": "too_slow",
                    "actual_time": actual_time,
                    "effective_time": recognized_time
                }

            # Existing normal record:
            # the original baseline remains fixed for the entire
            # repeat set.
            if actual_time < previous_record:
                return {
                    "status": "success",
                    "actual_time": actual_time,
                    "effective_time": recognized_time
                }

            return {
                "status": "too_slow",
                "actual_time": actual_time,
                "effective_time": recognized_time
            }

        # Start timer on first character.
        if start_time is None:
            start_time = time.perf_counter()

        position = len(typed)

        # Wrong character immediately fails and retries without a flash screen.
        if position >= len(word) or key != word[position]:
            actual_time = (
                time.perf_counter() - start_time
            )

            return {
                "status": "mistake",
                "actual_time": actual_time,
                "effective_time": None
            }

        typed += key

        elapsed = (
            time.perf_counter() - start_time
        )

        render_typing_screen(
            profile,
            word,
            word_number,
            total_words,
            typed,
            elapsed,
            previous_record,
            repeat_required,
            repeat_completed
        )


# ============================================================
# Train word
# ============================================================

def train_word(
    profile,
    word,
    word_number,
    total_words,
    repeat_required
):
    previous_record = profile["records"].get(word)

    # These are the successful qualifying times for this word.
    repeat_times = []

    while len(repeat_times) < repeat_required:
        result = attempt_word(
            profile,
            word,
            word_number,
            total_words,
            previous_record,
            repeat_required,
            len(repeat_times)
        )

        if result["status"] == "navigate":
            return result

        if result["status"] != "success":
            # The failed attempt is discarded. The repeat count
            # remains unchanged, and the same word immediately resets.
            continue

        repeat_times.append(
            result["effective_time"]
        )

    # Store the arithmetic mean of the successful attempts.
    average_time = sum(repeat_times) / len(repeat_times)

    # The 500 WPM ceiling must still apply to the stored average.
    average_time = max(
        average_time,
        max_wpm_time(word)
    )

    profile["records"][word] = average_time

    # Advance immediately after the repeat set is complete.
    profile["next_index"] = (
        profile["next_index"] + 1
    ) % total_words

    save_profile(profile)

    return {
        "status": "success",
        "record": average_time
    }


# ============================================================
# Trainer
# ============================================================

def run_trainer(profile, repeat_required):
    words = profile["words"]
    total_words = len(words)

    while True:
        index = profile["next_index"]
        word = words[index]

        result = train_word(
            profile,
            word,
            index + 1,
            total_words,
            repeat_required
        )

        if result["status"] == "navigate":
            if result["direction"] == "previous":
                move_word(profile, "previous")
            else:
                move_word(profile, "next")


# ============================================================
# CLI parsing
# ============================================================

def parse_repeat(value):
    try:
        repeat = int(value)

    except ValueError:
        raise ValueError(
            "--repeat must be a positive integer."
        )

    if repeat < 1:
        raise ValueError(
            "--repeat must be a positive integer."
        )

    return repeat


def parse_profile_args(args):
    if not args:
        raise ValueError("Missing profile name.")

    profile_name = None
    repeat_required = 1

    index = 0

    while index < len(args):
        argument = args[index]

        if argument == "--repeat":
            if index + 1 >= len(args):
                raise ValueError(
                    "--repeat requires a number."
                )

            repeat_required = parse_repeat(
                args[index + 1]
            )

            index += 2
            continue

        if argument.startswith("--repeat="):
            repeat_required = parse_repeat(
                argument.split("=", 1)[1]
            )

            index += 1
            continue

        if argument == "--profile":
            if index + 1 >= len(args):
                raise ValueError(
                    "--profile requires a profile name."
                )

            profile_name = args[index + 1]
            index += 2
            continue

        if argument.startswith("--profile="):
            profile_name = argument.split("=", 1)[1]
            index += 1
            continue

        raise ValueError(
            f"Unknown argument: {argument}"
        )

    if not profile_name:
        raise ValueError(
            "--profile requires a profile name."
        )

    return profile_name, repeat_required


# ============================================================
# Usage
# ============================================================

def print_usage():
    print(
        styled(
            "BURSTCLI",
            Style.BRIGHT_CYAN,
            bold=True
        )
    )

    print()
    print("Usage:")
    print()

    print(
        styled(
            "  burstcli --load <dataset>",
            Style.BRIGHT_WHITE
        )
    )
    print("      Create a profile from a dataset.")

    print()

    print(
        styled(
            "  burstcli --profile <name> [--repeat N]",
            Style.BRIGHT_WHITE
        )
    )
    print("      Run a profile.")
    print("      --repeat defaults to 1.")

    print()

    print(
        styled(
            "  burstcli --list",
            Style.BRIGHT_WHITE
        )
    )
    print("      List profiles.")

    print()
    print("Examples:")

    print(
        styled(
            "  burstcli --load mywords.txt",
            Style.BRIGHT_CYAN
        )
    )

    print(
        styled(
            "  burstcli --profile mywords",
            Style.BRIGHT_CYAN
        )
    )

    print(
        styled(
            "  burstcli --profile programming --repeat 4",
            Style.BRIGHT_CYAN
        )
    )


# ============================================================
# Main
# ============================================================

def main():
    enable_ansi()

    args = sys.argv[1:]

    if not args:
        print_usage()
        return

    # --list
    if args[0] == "--list":
        if len(args) != 1:
            print("Usage: burstcli --list")
            return

        list_profiles()
        return

    # --load
    if args[0] == "--load":
        if len(args) != 2:
            print(
                "Usage: "
                "burstcli --load <dataset>"
            )
            return

        create_profile_from_dataset(args[1])
        return

    # --profile
    if args[0] == "--profile":
        try:
            profile_name, repeat_required = parse_profile_args(
                args
            )

        except ValueError as error:
            print(
                styled(
                    f"Error: {error}",
                    Style.BRIGHT_RED
                )
            )
            print()
            print_usage()
            return

        profile = load_profile(profile_name)

        if profile is None:
            return

        # Save normalized records/words if needed.
        save_profile(profile)

        clear_screen()

        total_words = len(profile["words"])
        current_word = profile["next_index"] + 1

        repeat_text = (
            f"REPEAT: {repeat_required}"
            if repeat_required > 1
            else "REPEAT: 1"
        )

        lines = [
            centered_text(
                styled(
                    "BURSTCLI",
                    Style.BRIGHT_CYAN,
                    bold=True
                )
            ),
            "",
            centered_text(
                styled(
                    profile["name"],
                    Style.BRIGHT_WHITE,
                    bold=True
                )
            ),
            "",
            centered_text(
                "Resume: "
                + styled(
                    f"{current_word}/{total_words}",
                    Style.BRIGHT_CYAN,
                    bold=True
                )
            ),
            "",
            centered_text(
                styled(
                    repeat_text,
                    Style.BRIGHT_YELLOW
                    if repeat_required > 1
                    else Style.DIM,
                    bold=repeat_required > 1
                )
            ),
            "",
            centered_text(
                styled(
                    "500 WPM CEILING",
                    Style.DIM
                )
            ),
            "",
            centered_text(
                styled(
                    "← → navigate   |   any key to start",
                    Style.DIM
                )
            )
        ]

        print_panel(lines)

        try:
            wait_for_key()

            hide_cursor()

            run_trainer(
                profile,
                repeat_required
            )

        except KeyboardInterrupt:
            clear_screen()

            print(
                styled(
                    "BURSTCLI",
                    Style.BRIGHT_CYAN,
                    bold=True
                )
            )

            print()

            print(
                styled(
                    "Exited.",
                    Style.DIM
                )
            )

        finally:
            show_cursor()

        return

    # Unknown command.
    print(
        styled(
            f"Unknown command: {args[0]}",
            Style.BRIGHT_RED
        )
    )

    print()
    print_usage()


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":
    main()
