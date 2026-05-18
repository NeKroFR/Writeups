import math
import os
import random
import sys
from typing import Optional


ROUNDS = 3000
K_GUESSES = 6
FLAG_WIN_STREAK = 20
FLAG = os.getenv("FLAG", "EPFL{FAKE_FLAG_FOR_TESTING}")
CORPUS_PATH = os.getenv("CORPUS_PATH", "wordlist.txt")


COLORS = {
    "G": "\033[92m",  # Correct letter, correct place
    "Y": "\033[93m",  # Correct letter, wrong place
    "B": "\033[90m",  # Letter not in solution
    "RESET": "\033[0m",  # Resets color to default
    "RED": "\033[1;31m",
    "BLUE": "\033[1;34m",
    "PURPLE": "\033[1;35m",
}
COLORS["GREEN"] = COLORS["G"]


def send(msg):
    print(msg, flush=True)


def recv(prompt: str):
    try:
        return input(prompt).strip().upper()
    except (EOFError, KeyboardInterrupt):
        send("\nQuitting...")
        sys.exit(0)


def get_wordle_pattern(guess: str, answer: str):
    result = ["B"] * 5
    answer_chars: list[str | None] = list(answer)
    for i in range(5):
        if guess[i] == answer[i]:
            result[i] = "G"
            answer_chars[i] = None

    for i in range(5):
        if result[i] == "G":
            continue

        if guess[i] in answer_chars:
            result[i] = "Y"
            answer_chars[answer_chars.index(guess[i])] = None

    # ANSI color mapping for better UX
    # G: Green, Y: Yellow, B: Gray/Black

    colored_guess = "".join(
        COLORS[c] + guess[i] + COLORS["RESET"] for i, c in enumerate(result)
    )
    return "".join(result), colored_guess


def get_next_word(rng: random.Random, cache: list[int], wordlist: list[str]):
    if not cache:
        value = rng.getrandbits(32)
        cache.extend([(value >> 16) & 0xFFFF, value & 0xFFFF])
    idx_raw = cache.pop(0)
    useful_bits = math.ceil(math.log2(len(wordlist)))
    idx = idx_raw & ((1 << useful_bits) - 1)
    if idx >= len(wordlist):
        idx ^= 1 << (useful_bits - 1)
    # Return the word and the next 2 bits (bits 13 and 12 of the chunk)
    return wordlist[idx], (idx_raw >> 12) & 3


def play_round(answer: str, valid_words) -> Optional[int]:
    for attempt in range(K_GUESSES):
        guess = recv("> ")
        if len(guess) != 5 or guess not in valid_words:
            send("INVALID")
            continue
        pat, colored_guess = get_wordle_pattern(guess, answer)
        send(colored_guess)
        send(f"Pattern: {pat}")
        if answer == guess:
            return attempt + 1

    return None


def main():
    rng = random.Random(os.urandom(32))
    cache = []

    # Load corpus
    with open(CORPUS_PATH) as f:
        words = [line.strip().upper() for line in f]

    allowed_words = set(words)
    streak = 0

    send(COLORS["RED"] + "Present Day... Present Time! HAHAHAHAHAHA" + COLORS["RESET"])
    send(
        f"Welcome to the {COLORS['BLUE']}Wordle{COLORS['RESET']}. Are you truly connected?"
    )
    send("No matter where you are, everyone is always connected.\n")

    for round in range(ROUNDS):
        send(f"{COLORS['PURPLE']}LAYER {round + 1:04}{COLORS['RESET']}")
        answer, leak = get_next_word(rng, cache, words)
        attempts = play_round(answer, allowed_words)
        send("")
        if attempts:
            send(f"{COLORS['GREEN']}CONNECTED{COLORS['RESET']}")
            send(f"LEAK: {leak:02b}")
        else:
            send(f"{COLORS['RED']}DISCONNECTED{COLORS['RESET']}")

        if attempts == 1:
            streak += 1
        else:
            streak = 0

        if streak == FLAG_WIN_STREAK:
            send(
                f"\nThe border between the {COLORS['GREEN']}Wordle{COLORS['RESET']} and the real world has blurred."
            )

            _, rng = get_next_word(rng, cache, words)
            ans = recv("Answer the last enigma: ")
            if ans == "LAIN"[rng]:
                send(f"Here is your truth: {FLAG}")
            exit(0)

        send("")


if __name__ == "__main__":
    main()
