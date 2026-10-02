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


# Matches ANSI color/style escape sequences.
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def visible_len(text):
    """
    Return the visible length of a string.

    ANSI escape sequences do not occupy visible terminal columns,
    so they are removed before calculating the length.
    """

    return len(
        ANSI_RE.sub("", text)
    )


def styled(
    text,
    color="",
    bold=False,
    dim=False
):

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
    """
    Enable ANSI escape sequences on Windows where possible.
    """

    if os.name != "nt":
        return

    try:

        import ctypes

        kernel32 = ctypes.windll.kernel32

        handle = kernel32.GetStdHandle(-11)

        mode = ctypes.c_uint32()

        if kernel32.GetConsoleMode(
            handle,
            ctypes.byref(mode)
        ):

            # ENABLE_VIRTUAL_TERMINAL_PROCESSING
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
    """
    Clear terminal and move cursor to top-left.
    """

    sys.stdout.write(
        "\033[2J\033[H"
    )

    sys.stdout.flush()


def hide_cursor():

    sys.stdout.write(
        "\033[?25l"
    )

    sys.stdout.flush()


def show_cursor():

    sys.stdout.write(
        "\033[?25h"
    )

    sys.stdout.flush()


def move_cursor_home():

    sys.stdout.write(
        "\033[H"
    )

    sys.stdout.flush()


def read_key():

    return msvcrt.getwch()


def wait_for_key():

    msvcrt.getwch()


# ============================================================
# Fixed-width text helpers
# ============================================================

def pad_visible(
    text,
    width,
    align="left"
):
    """
    Pad a string to an exact visible width.

    ANSI color codes are ignored when calculating width.
    """

    current_length = visible_len(text)

    if current_length >= width:

        # Avoid cutting ANSI escape sequences.
        # If the text is too long, strip styling before truncating.
        if current_length > width:

            plain = ANSI_RE.sub(
                "",
                text
            )

            return plain[:width]

        return text

    padding = width - current_length

    if align == "right":

        return (
            " " * padding
            + text
        )

    if align == "center":

        left = padding // 2
        right = padding - left

        return (
            " " * left
            + text
            + " " * right
        )

    return (
        text
        + " " * padding
    )


def centered_text(
    text,
    width=INNER_WIDTH
):

    return pad_visible(
        text,
        width,
        "center"
    )


# ============================================================
# Panel UI
# ============================================================

BORDER_TOP = (
    "╭"
    + "─" * (UI_WIDTH - 2)
    + "╮"
)

BORDER_BOTTOM = (
    "╰"
    + "─" * (UI_WIDTH - 2)
    + "╯"
)

BORDER_SEPARATOR = (
    "├"
    + "─" * (UI_WIDTH - 2)
    + "┤"
)


def panel_line(content=""):
    """
    Create an exact-width panel line.

    Result is always exactly UI_WIDTH visible characters.
    """

    content = pad_visible(
        content,
        INNER_WIDTH,
        "left"
    )

    return (
        "│"
        + content
        + "│"
    )


def print_panel(lines):

    print(BORDER_TOP)

    for line in lines:
        print(
            panel_line(line)
        )

    print(BORDER_BOTTOM)


# ============================================================
# Profile paths
# ============================================================

def profile_path(profile_name):

    return Path(
        f"{profile_name}{PROFILE_EXTENSION}"
    )


# ============================================================
# Dataset
# ============================================================

def load_dataset_file(path):
    """
    Load comma, whitespace, or newline separated words.
    """

    text = path.read_text(
        encoding="utf-8"
    )

    text = text.replace(
        ",",
        " "
    )

    words = text.split()

    if not words:

        raise ValueError(
            "Dataset contains no words."
        )

    return words


# ============================================================
# Profile creation
# ============================================================

def create_profile_from_dataset(
    dataset_path
):

    dataset_path = Path(
        dataset_path
    )

    if not dataset_path.exists():

        print(
            styled(
                f"Dataset not found: {dataset_path}",
                Style.BRIGHT_RED
            )
        )

        return False

    try:

        words = load_dataset_file(
            dataset_path
        )

    except (
        OSError,
        ValueError
    ) as error:

        print(
            styled(
                f"Error loading dataset: {error}",
                Style.BRIGHT_RED
            )
        )

        return False

    profile_name = dataset_path.stem

    output_path = profile_path(
        profile_name
    )

    if output_path.exists():

        print(
            styled(
                f"Profile already exists: {output_path}",
                Style.BRIGHT_YELLOW
            )
        )

        print()

        answer = input(
            "Overwrite it? [y/N]: "
        ).strip().lower()

        if answer != "y":

            print(
                "Profile not created."
            )

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
            json.dumps(
                profile,
                indent=4
            ),
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

    print(
        "Run it with:"
    )

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

    path = profile_path(
        profile_name
    )

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
            + styled(
                "--list",
                Style.BRIGHT_CYAN
            )
            + " to see available profiles."
        )

        return None

    try:

        profile = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except (
        OSError,
        json.JSONDecodeError
    ) as error:

        print(
            styled(
                f"Could not load profile: {error}",
                Style.BRIGHT_RED
            )
        )

        return None

    if not isinstance(
        profile,
        dict
    ):

        print(
            styled(
                "Invalid profile format.",
                Style.BRIGHT_RED
            )
        )

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

    if (
        not isinstance(words, list)
        or not words
    ):

        print(
            styled(
                "Profile contains no words.",
                Style.BRIGHT_RED
            )
        )

        return None

    if not isinstance(
        profile["next_index"],
        int
    ):

        profile["next_index"] = 0

    profile["next_index"] %= len(words)

    for word in words:

        if word not in profile["records"]:

            profile["records"][word] = None

    normalize_profile_records(
        profile
    )

    return profile


def save_profile(profile):

    path = profile_path(
        profile["name"]
    )

    temp_path = path.with_suffix(
        ".tmp"
    )

    temp_path.write_text(
        json.dumps(
            profile,
            indent=4
        ),
        encoding="utf-8"
    )

    temp_path.replace(
        path
    )


# ============================================================
# Profile listing
# ============================================================

def list_profiles():

    profiles = sorted(
        Path(".").glob("*.json")
    )

    valid_profiles = []

    for path in profiles:

        try:

            profile = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )

        except (
            OSError,
            json.JSONDecodeError
        ):

            continue

        if not isinstance(
            profile,
            dict
        ):

            continue

        if (
            "words" not in profile
            or "records" not in profile
        ):

            continue

        valid_profiles.append(
            (
                path,
                profile
            )
        )

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

    print(
        styled(
            "─" * 64,
            Style.DIM
        )
    )

    print()

    if not valid_profiles:

        print(
            styled(
                "No profiles found.",
                Style.YELLOW
            )
        )

        print()

        print(
            "Create one with:"
        )

        print(
            styled(
                "  burstcli --load mywords.txt",
                Style.BRIGHT_CYAN
            )
        )

        return

    for index, (
        path,
        profile
    ) in enumerate(
        valid_profiles,
        start=1
    ):

        name = profile.get(
            "name",
            path.stem
        )

        words = profile.get(
            "words",
            []
        )

        next_index = profile.get(
            "next_index",
            0
        )

        print(
            f"  {styled(str(index), Style.DIM)}  "
            f"{styled(name, Style.BRIGHT_WHITE, bold=True)}"
        )

        print(
            f"      Words   : {len(words)}"
        )

        print(
            f"      Progress: "
            f"{next_index + 1}/{len(words)}"
        )

        print(
            f"      File    : {path.name}"
        )

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

    return (
        len(word)
        * SECONDS_PER_CHARACTER_AT_MAX_WPM
    )


def effective_time(
    word,
    actual_seconds
):

    return max(
        actual_seconds,
        max_wpm_time(word)
    )


def calculate_wpm(
    word,
    seconds
):

    if seconds <= 0:

        return MAX_WPM

    minutes = seconds / 60

    wpm = (
        (len(word) / 5)
        / minutes
    )

    return min(
        wpm,
        MAX_WPM
    )


def normalize_record(
    word,
    seconds
):

    return max(
        float(seconds),
        max_wpm_time(word)
    )


def normalize_profile_records(
    profile
):

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

        except (
            TypeError,
            ValueError
        ):

            records[word] = None


def is_maxed(
    word,
    record
):

    if record is None:

        return False

    threshold = max_wpm_time(
        word
    )

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


def format_wpm(
    word,
    seconds
):

    return (
        f"{calculate_wpm(word, seconds):.1f}"
        f" WPM"
    )


def progress_bar(
    current,
    total,
    width=PROGRESS_WIDTH
):

    if total <= 0:

        return ""

    ratio = current / total

    ratio = max(
        0.0,
        min(
            ratio,
            1.0
        )
    )

    filled = int(
        ratio * width
    )

    filled = min(
        filled,
        width
    )

    empty = (
        width - filled
    )

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

def render_word_progress(
    word,
    typed
):
    """
    Render the target word in one fixed-width field.

    Correctly typed characters:
        GREEN

    Current character:
        YELLOW

    Remaining characters:
        DIM

    The total visible width is always exactly len(word).
    """

    output = ""

    typed_length = len(
        typed
    )

    for index, character in enumerate(
        word
    ):

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
    previous_record
):

    clear_screen()

    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------

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
        + " " * max(
            1,
            header_space
        )
        + header_right
    )

    print(
        panel_line(
            header_content
        )
    )

    # Profile name.
    print(
        panel_line(
            styled(
                profile["name"],
                Style.DIM
            )
        )
    )

    print(
        BORDER_SEPARATOR
    )

    # --------------------------------------------------------
    # Target word
    # --------------------------------------------------------

    print(
        panel_line()
    )

    target_display = styled(
        word,
        Style.BRIGHT_WHITE,
        bold=True
    )

    print(
        panel_line(
            centered_text(
                target_display
            )
        )
    )

    print(
        panel_line()
    )

    # --------------------------------------------------------
    # Typed progress
    # --------------------------------------------------------

    typed_display = render_word_progress(
        word,
        typed
    )

    print(
        panel_line(
            centered_text(
                typed_display
            )
        )
    )

    print(
        panel_line()
    )

    # --------------------------------------------------------
    # Timer
    # --------------------------------------------------------

    if elapsed is not None:

        current_time = elapsed

        recognized_time = effective_time(
            word,
            current_time
        )

        current_wpm = calculate_wpm(
            word,
            recognized_time
        )

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

    print(
        panel_line()
    )

    # --------------------------------------------------------
    # Record
    # --------------------------------------------------------

    if previous_record is None:

        record_text = (
            "Record: "
            + styled(
                "--",
                Style.DIM
            )
        )

    elif is_maxed(
        word,
        previous_record
    ):

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
                format_wpm(
                    word,
                    previous_record
                ),
                Style.BRIGHT_WHITE
            )
        )

    print(
        panel_line(
            centered_text(
                record_text
            )
        )
    )

    print(
        panel_line()
    )

    # --------------------------------------------------------
    # Progress bar
    # --------------------------------------------------------

    bar = progress_bar(
        word_number,
        total_words
    )

    print(
        panel_line(
            centered_text(
                bar
            )
        )
    )

    print(
        panel_line()
    )

    # --------------------------------------------------------
    # Instructions
    # --------------------------------------------------------

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

    print(
        BORDER_BOTTOM
    )

    sys.stdout.flush()


# ============================================================
# Result screens
# ============================================================

def render_result(
    profile,
    word,
    word_number,
    total_words,
    result,
    previous_record
):

    clear_screen()

    status = result["status"]

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    if status == "success":

        new_record = result[
            "new_record"
        ]

        maxed = is_maxed(
            word,
            new_record
        )

        lines = []

        lines.append(
            styled(
                profile["name"],
                Style.DIM
            )
        )

        lines.append("")

        lines.append(
            centered_text(
                styled(
                    f"{word_number}/{total_words}",
                    Style.DIM
                )
            )
        )

        lines.append("")

        lines.append(
            centered_text(
                styled(
                    "✓ SUCCESS",
                    Style.BRIGHT_GREEN,
                    bold=True
                )
            )
        )

        lines.append("")

        lines.append(
            centered_text(
                styled(
                    word,
                    Style.BRIGHT_WHITE,
                    bold=True
                )
            )
        )

        lines.append("")

        lines.append(
            centered_text(
                styled(
                    format_ms(new_record),
                    Style.BRIGHT_GREEN,
                    bold=True
                )
            )
        )

        lines.append(
            centered_text(
                styled(
                    format_wpm(
                        word,
                        new_record
                    ),
                    Style.BRIGHT_GREEN,
                    bold=True
                )
            )
        )

        if maxed:

            lines.append("")

            lines.append(
                centered_text(
                    styled(
                        "★ 500 WPM MAXED ★",
                        Style.BRIGHT_GREEN,
                        bold=True
                    )
                )
            )

        lines.append("")

        if word_number == total_words:

            lines.append(
                centered_text(
                    styled(
                        "Dataset complete → word 1",
                        Style.BRIGHT_CYAN
                    )
                )
            )

        else:

            lines.append(
                centered_text(
                    styled(
                        f"Next → "
                        f"{word_number + 1}/{total_words}",
                        Style.BRIGHT_CYAN
                    )
                )
            )

        lines.append("")

        lines.append(
            centered_text(
                styled(
                    "Press any key",
                    Style.DIM
                )
            )
        )

        print_panel(
            lines
        )

        return

    # --------------------------------------------------------
    # MISTAKE
    # --------------------------------------------------------

    if status == "mistake":

        lines = [
            styled(
                profile["name"],
                Style.DIM
            ),

            "",

            centered_text(
                styled(
                    f"{word_number}/{total_words}",
                    Style.DIM
                )
            ),

            "",

            centered_text(
                styled(
                    "✗ MISTAKE",
                    Style.BRIGHT_RED,
                    bold=True
                )
            ),

            "",

            centered_text(
                styled(
                    "The word must be typed perfectly.",
                    Style.BRIGHT_RED
                )
            ),

            "",

            centered_text(
                styled(
                    "Same word again",
                    Style.BRIGHT_YELLOW
                )
            ),

            "",

            centered_text(
                styled(
                    "Press any key",
                    Style.DIM
                )
            )
        ]

        print_panel(
            lines
        )

        return

    # --------------------------------------------------------
    # TOO SLOW
    # --------------------------------------------------------

    if status == "too_slow":

        recognized_time = result[
            "effective_time"
        ]

        lines = [
            styled(
                profile["name"],
                Style.DIM
            ),

            "",

            centered_text(
                styled(
                    f"{word_number}/{total_words}",
                    Style.DIM
                )
            ),

            "",

            centered_text(
                styled(
                    "TOO SLOW",
                    Style.BRIGHT_YELLOW,
                    bold=True
                )
            ),

            "",

            centered_text(
                styled(
                    format_ms(
                        recognized_time
                    ),
                    Style.BRIGHT_YELLOW,
                    bold=True
                )
            ),

            centered_text(
                styled(
                    format_wpm(
                        word,
                        recognized_time
                    ),
                    Style.BRIGHT_YELLOW
                )
            ),

            ""
        ]

        if is_maxed(
            word,
            previous_record
        ):

            lines.append(
                centered_text(
                    styled(
                        "Target: "
                        + format_ms(
                            max_wpm_time(word)
                        )
                        + " / 500 WPM",
                        Style.BRIGHT_CYAN
                    )
                )
            )

        else:

            lines.append(
                centered_text(
                    styled(
                        "Record: "
                        + format_ms(
                            previous_record
                        )
                        + " / "
                        + format_wpm(
                            word,
                            previous_record
                        ),
                        Style.BRIGHT_CYAN
                    )
                )
            )

        lines.extend([
            "",

            centered_text(
                styled(
                    "Same word again",
                    Style.BRIGHT_YELLOW
                )
            ),

            "",

            centered_text(
                styled(
                    "Press any key",
                    Style.DIM
                )
            )
        ])

        print_panel(
            lines
        )


# ============================================================
# Word attempt
# ============================================================

def attempt_word(
    profile,
    word,
    word_number,
    total_words,
    previous_record
):

    typed = ""

    start_time = None

    # Initial screen.
    render_typing_screen(
        profile,
        word,
        word_number,
        total_words,
        typed,
        None,
        previous_record
    )

    while True:

        key = read_key()

        # ----------------------------------------------------
        # Ctrl+C
        # ----------------------------------------------------

        if key == "\x03":

            raise KeyboardInterrupt

        # ----------------------------------------------------
        # Backspace
        #
        # Backspace is deliberately disabled.
        # It immediately fails the attempt.
        # ----------------------------------------------------

        if key == "\x08":

            result = {
                "status": "mistake",
                "actual_time": None,
                "effective_time": None,
                "new_record": None
            }

            render_result(
                profile,
                word,
                word_number,
                total_words,
                result,
                previous_record
            )

            return result

        # ----------------------------------------------------
        # Special keys
        # ----------------------------------------------------

        if key in (
            "\x00",
            "\xe0"
        ):

            read_key()

            result = {
                "status": "mistake",
                "actual_time": None,
                "effective_time": None,
                "new_record": None
            }

            render_result(
                profile,
                word,
                word_number,
                total_words,
                result,
                previous_record
            )

            return result

        # ----------------------------------------------------
        # Space = submit
        # ----------------------------------------------------

        if key == " ":

            if start_time is None:

                result = {
                    "status": "mistake",
                    "actual_time": None,
                    "effective_time": None,
                    "new_record": None
                }

                render_result(
                    profile,
                    word,
                    word_number,
                    total_words,
                    result,
                    previous_record
                )

                return result

            actual_time = (
                time.perf_counter()
                - start_time
            )

            # Incorrect final word.
            if typed != word:

                result = {
                    "status": "mistake",
                    "actual_time": actual_time,
                    "effective_time": effective_time(
                        word,
                        actual_time
                    ),
                    "new_record": None
                }

                render_result(
                    profile,
                    word,
                    word_number,
                    total_words,
                    result,
                    previous_record
                )

                return result

            recognized_time = effective_time(
                word,
                actual_time
            )

            threshold = max_wpm_time(
                word
            )

            # ------------------------------------------------
            # First record.
            # ------------------------------------------------

            if previous_record is None:

                result = {
                    "status": "success",
                    "actual_time": actual_time,
                    "effective_time": recognized_time,
                    "new_record": recognized_time
                }

                render_result(
                    profile,
                    word,
                    word_number,
                    total_words,
                    result,
                    previous_record
                )

                return result

            # ------------------------------------------------
            # Already maxed.
            # ------------------------------------------------

            if is_maxed(
                word,
                previous_record
            ):

                if actual_time <= (
                    threshold + EPSILON
                ):

                    result = {
                        "status": "success",
                        "actual_time": actual_time,
                        "effective_time": threshold,
                        "new_record": threshold
                    }

                else:

                    result = {
                        "status": "too_slow",
                        "actual_time": actual_time,
                        "effective_time": recognized_time,
                        "new_record": None
                    }

                render_result(
                    profile,
                    word,
                    word_number,
                    total_words,
                    result,
                    previous_record
                )

                return result

            # ------------------------------------------------
            # Normal record.
            # ------------------------------------------------

            if actual_time < previous_record:

                result = {
                    "status": "success",
                    "actual_time": actual_time,
                    "effective_time": recognized_time,
                    "new_record": recognized_time
                }

            else:

                result = {
                    "status": "too_slow",
                    "actual_time": actual_time,
                    "effective_time": recognized_time,
                    "new_record": None
                }

            render_result(
                profile,
                word,
                word_number,
                total_words,
                result,
                previous_record
            )

            return result

        # ----------------------------------------------------
        # Start timer on first character.
        # ----------------------------------------------------

        if start_time is None:

            start_time = time.perf_counter()

        # ----------------------------------------------------
        # Check character.
        # ----------------------------------------------------

        position = len(typed)

        if (
            position >= len(word)
            or key != word[position]
        ):

            actual_time = (
                time.perf_counter()
                - start_time
            )

            result = {
                "status": "mistake",
                "actual_time": actual_time,
                "effective_time": None,
                "new_record": None
            }

            render_result(
                profile,
                word,
                word_number,
                total_words,
                result,
                previous_record
            )

            return result

        typed += key

        # ----------------------------------------------------
        # Live UI update.
        # ----------------------------------------------------

        elapsed = (
            time.perf_counter()
            - start_time
        )

        render_typing_screen(
            profile,
            word,
            word_number,
            total_words,
            typed,
            elapsed,
            previous_record
        )


# ============================================================
# Train word
# ============================================================

def train_word(
    profile,
    word,
    word_number,
    total_words
):

    previous_record = (
        profile["records"].get(word)
    )

    while True:

        result = attempt_word(
            profile,
            word,
            word_number,
            total_words,
            previous_record
        )

        # ----------------------------------------------------
        # Mistake / too slow.
        # ----------------------------------------------------

        if result["status"] != "success":

            wait_for_key()

            continue

        # ----------------------------------------------------
        # Successful completion.
        # ----------------------------------------------------

        new_record = result[
            "new_record"
        ]

        profile["records"][word] = (
            new_record
        )

        # ----------------------------------------------------
        # Advance immediately.
        # ----------------------------------------------------

        next_index = (
            profile["next_index"] + 1
        ) % total_words

        profile["next_index"] = (
            next_index
        )

        save_profile(
            profile
        )

        wait_for_key()

        return


# ============================================================
# Trainer
# ============================================================

def run_trainer(profile):

    words = profile["words"]

    total_words = len(words)

    while True:

        index = profile["next_index"]

        word = words[index]

        train_word(
            profile,
            word,
            index + 1,
            total_words
        )


# ============================================================
# CLI
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

    print(
        "Usage:"
    )

    print()

    print(
        styled(
            "  burstcli --load <dataset>",
            Style.BRIGHT_WHITE
        )
    )

    print(
        "      Create a profile from a dataset."
    )

    print()

    print(
        styled(
            "  burstcli --profile <name>",
            Style.BRIGHT_WHITE
        )
    )

    print(
        "      Run a profile."
    )

    print()

    print(
        styled(
            "  burstcli --list",
            Style.BRIGHT_WHITE
        )
    )

    print(
        "      List profiles."
    )

    print()

    print(
        "Examples:"
    )

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


# ============================================================
# Main
# ============================================================

def main():

    enable_ansi()

    args = sys.argv[1:]

    if not args:

        print_usage()

        return

    # --------------------------------------------------------
    # --list
    # --------------------------------------------------------

    if args[0] == "--list":

        if len(args) != 1:

            print(
                "Usage: burstcli --list"
            )

            return

        list_profiles()

        return

    # --------------------------------------------------------
    # --load
    # --------------------------------------------------------

    if args[0] == "--load":

        if len(args) != 2:

            print(
                "Usage: "
                "burstcli --load <dataset>"
            )

            return

        create_profile_from_dataset(
            args[1]
        )

        return

    # --------------------------------------------------------
    # --profile
    # --------------------------------------------------------

    if args[0] == "--profile":

        if len(args) != 2:

            print(
                "Usage: "
                "burstcli --profile <name>"
            )

            return

        profile = load_profile(
            args[1]
        )

        if profile is None:

            return

        # Save normalized records.
        save_profile(
            profile
        )

        clear_screen()

        total_words = len(
            profile["words"]
        )

        current_word = (
            profile["next_index"] + 1
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
                    "500 WPM CEILING",
                    Style.DIM
                )
            ),

            "",

            centered_text(
                styled(
                    "Press any key to start",
                    Style.DIM
                )
            )
        ]

        print_panel(
            lines
        )

        try:

            wait_for_key()

            hide_cursor()

            run_trainer(
                profile
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

    # --------------------------------------------------------
    # Unknown command.
    # --------------------------------------------------------

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