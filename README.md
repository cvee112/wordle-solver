# 🟩 Wordle Solver

An optimal Wordle solver using **entropy maximization** — the mathematically best strategy for solving Wordle in the fewest guesses.

## Features

- **Information-theoretic optimal guessing** — maximizes expected information gain at each step
- **14,855 word vocabulary** — comprehensive 5-letter English word list
- **Dual recommendations** — shows both strategic guesses and best possible answers
- **Interactive & batch modes** — use interactively or script it
- **Hard mode support** — restricts suggestions to possible answers only
- **No external dependencies** — pure Python standard library

## Installation

```bash
git clone https://github.com/yourusername/wordle-solver.git
cd wordle-solver
```

No dependencies required — runs on Python 3.8+.

## Quick Start

### Interactive Mode

```bash
python wordle_solver.py
```

Then enter your guesses and the feedback pattern:
- `g` = 🟩 Green (correct position)
- `y` = 🟨 Yellow (wrong position)
- `x` = ⬛ Gray (not in word)

**Example session:**
```
📝 GUESS #1
   Enter your guess: crane
   Enter the pattern (g/y/x): xxxyx
   Result: CRANE → ⬛⬛⬛🟨⬛

════════════════════════════════════════════════════════════
                    TOP RECOMMENDATIONS
════════════════════════════════════════════════════════════
Rank  Word       Entropy    Exp.Left   Possible?
────────────────────────────────────────────────────────────
1     TONUS      5.555      15.9       ✓ Yes
2     DINOS      5.541      15.1       ✓ Yes
3     DOITS      5.521      17.5         No
...
```

### Batch Mode

```bash
python wordle_solver.py "crane:xxxyx" "tonus:xygxg"
```

### Commands (Interactive Mode)

| Command | Description |
|---------|-------------|
| `/hint` or `/h` | Show optimal recommendations |
| `/history` or `/hi` | Show guess history |
| `/reset` or `/r` | Start over |
| `/quit` or `/q` | Exit |

Commands use `/` prefix to avoid collision with valid words like "reset".

### Options

```bash
# Use hard mode (only suggest possible answers)
python wordle_solver.py --hard

# Use a custom word list
python wordle_solver.py -w /path/to/mywords.txt

# Combine options
python wordle_solver.py --hard -w custom.txt "crane:xxxyx"
```

## How It Works

### The Algorithm: Entropy Maximization

The solver uses **information theory** to find the optimal guess. For each candidate word, it calculates the **expected information gain** (entropy):

```
Entropy = -Σ p(pattern) × log₂(p(pattern))
```

Where `p(pattern)` is the probability of each possible feedback pattern.

**Why entropy?**

A good guess splits the remaining possibilities into many small, roughly equal groups. Entropy quantifies this "spread" — higher entropy means more information gained on average.

### Example

With 100 remaining words:

| Guess | Pattern Distribution | Entropy |
|-------|---------------------|---------|
| Word A | 50/50 split | 1.0 bit |
| Word B | 90/10 split | 0.47 bits |

**Word A is better** — it eliminates more possibilities on average.

### Pattern Computation

The solver correctly handles Wordle's rules for duplicate letters:

```python
def get_pattern(guess: str, answer: str) -> str:
    # First pass: mark greens (exact matches)
    # Second pass: mark yellows (right letter, wrong position)
    # Greens take priority over yellows
```

### Normal vs Hard Mode

| Mode | Behavior |
|------|----------|
| **Normal** | Considers all 14,855 words — may suggest "strategic" guesses that can't be the answer but eliminate more possibilities |
| **Hard** (`--hard`) | Only suggests words that could be the answer — matches Wordle's hard mode rules |

## Output Explained

```
════════════════════════════════════════════════════════════
                    TOP RECOMMENDATIONS
════════════════════════════════════════════════════════════
Rank  Word       Entropy    Exp.Left   Possible?
────────────────────────────────────────────────────────────
1     PISKY      3.852      1.2          No      ← Best strategic guess
2     CUSPY      3.455      1.7        ✓ Yes    ← Best possible answer
...

────────────────────────────────────────────────────────────
         TOP POSSIBLE ANSWERS (if you must guess one)
────────────────────────────────────────────────────────────
1     CUSPY      3.455      1.7                 ← Use this to potentially win now
...

📊 Remaining possible answers: 17
   (sorted by entropy, best first)
   CUSPY, CUSPS, CISSY, ...
```

- **Entropy**: Expected information gain in bits (higher = better)
- **Exp.Left**: Expected remaining words after this guess (lower = better)
- **Possible?**: Whether this word could be the actual answer

## Recommended Opening Words

Based on entropy analysis against the full word list:

| Word | Entropy |
|------|---------|
| SALET | ~6.1 bits |
| REAST | ~6.1 bits |
| CRATE | ~5.9 bits |
| TRACE | ~5.9 bits |
| SLATE | ~5.8 bits |
| CRANE | ~5.5 bits |

## Custom Word Lists

The solver loads `words.txt` from the same directory by default. To use a custom list:

1. Create a text file with one 5-letter word per line
2. Pass it with `-w`:

```bash
python wordle_solver.py -w my_words.txt
```

## Performance

- **First guess**: ~15,000 × 15,000 pattern computations (~3-5 seconds)
- **Later guesses**: Much faster as remaining words decrease
- **Memory**: ~2 MB for word list

## File Structure

```
wordle-solver/
├── wordle_solver.py   # Main solver script
├── words.txt          # Word list (14,855 words)
├── README.md          # This file
├── requirements.txt   # Dependencies (none required)
└── LICENSE            # MIT License
```

## API Usage

```python
from wordle_solver import WordleSolver

# Create solver
solver = WordleSolver(hard_mode=False, word_file="words.txt")

# Apply guesses
solver.apply_guess("crane", "xxxyx")
solver.apply_guess("tonus", "xygxg")

# Get recommendations
recommendations = solver.get_best_guess(top_n=5, show_progress=False)
for word, entropy, expected, is_possible in recommendations:
    print(f"{word}: entropy={entropy:.3f}, possible={is_possible}")

# Check remaining possibilities
print(f"Remaining: {len(solver.possible_answers)}")
print(solver.possible_answers)

# Reset for new game
solver.reset()
```

## License

MIT License — see [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Some ideas:

- [ ] Precompute opening word entropies for faster startup
- [ ] Add multi-step lookahead (computationally expensive but more optimal)
- [ ] Web interface
- [ ] Support for other Wordle variants (6-letter, etc.)

## Acknowledgments

- Algorithm inspired by [3Blue1Brown's Wordle analysis](https://www.youtube.com/watch?v=v68zYyaEmEA)
- Information theory foundations from Claude Shannon
