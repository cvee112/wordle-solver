# 🟩 Wordle Solver

An optimal Wordle solver with two modes: **entropy maximization** (mathematically optimal) and **bot mode** (mimics NYT Wordle Bot behavior).

## Features

- **Two solving modes:**
  - **Entropy mode** (default) — maximizes expected information gain
  - **Bot mode** — mimics NYT Wordle Bot with curated solutions + word frequency
- **14,855 word vocabulary** — comprehensive 5-letter English word list
- **2,315 curated solutions** — official Wordle answer list with frequency data (bot mode)
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
              TOP RECOMMENDATIONS (ENTROPY MODE)
════════════════════════════════════════════════════════════
Rank  Word       Entropy    Exp.Left   Possible?
────────────────────────────────────────────────────────────
1     TONUS      5.555      15.9       ✓ Yes
2     DINOS      5.541      15.1       ✓ Yes
3     DOITS      5.521      17.5         No
...
```

### Bot Mode (Mimics NYT Wordle Bot)

```bash
python wordle_solver.py --bot
```

Bot mode uses the official ~2,315 word solutions list and scores by expected remaining solutions with word frequency as a tiebreaker — closely matching how the NYT Wordle Bot evaluates guesses.

```
════════════════════════════════════════════════════════════
              TOP RECOMMENDATIONS (🤖 BOT MODE)
════════════════════════════════════════════════════════════
Rank  Word       Exp.Left   Freq.Score Possible?
────────────────────────────────────────────────────────────
1     SLATE      21.3       0.745      ✓ Yes
2     CRANE      22.1       0.698      ✓ Yes
...
```

### Batch Mode

```bash
# Entropy mode
python wordle_solver.py "crane:xxxyx" "tonus:xygxg"

# Bot mode
python wordle_solver.py --bot "crane:xxxyx" "tonus:xygxg"
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
# Bot mode (mimic NYT Wordle Bot)
python wordle_solver.py --bot

# Hard mode (only suggest possible answers)
python wordle_solver.py --hard

# Custom word list (valid guesses)
python wordle_solver.py -w /path/to/mywords.txt

# Custom solutions file (for bot mode)
python wordle_solver.py --bot -s /path/to/solutions.csv

# Combine options
python wordle_solver.py --bot --hard "crane:xxxyx"
```

## Modes Explained

### Entropy Mode (Default)

Uses **information theory** to find the optimal guess by maximizing expected information gain:

```
Entropy = -Σ p(pattern) × log₂(p(pattern))
```

- Considers all 14,855 words as potential answers
- Maximizes entropy (information gained per guess)
- May suggest "strategic" words that can't be the answer but eliminate more possibilities

### Bot Mode (`--bot`)

Mimics **NYT Wordle Bot** scoring:

- Uses curated 2,315-word solutions list as potential answers
- Minimizes expected remaining solutions
- Uses word frequency (from Google's corpus) as tiebreaker
- Prefers common English words when scores are close

| Aspect | Entropy Mode | Bot Mode |
|--------|--------------|----------|
| Answer pool | 14,855 words | 2,315 curated |
| Scoring | Maximize entropy | Minimize expected remaining |
| Tiebreaker | Letter frequency | Word frequency |
| Best for | Mathematically optimal | Matching Wordle Bot |

### Hard Mode (`--hard`)

In either mode, `--hard` restricts suggestions to only words that could be the answer (matching Wordle's hard mode rules).

## How It Works

### Pattern Computation

The solver correctly handles Wordle's rules for duplicate letters:

```python
def get_pattern(guess: str, answer: str) -> str:
    # First pass: mark greens (exact matches)
    # Second pass: mark yellows (right letter, wrong position)
    # Greens take priority over yellows
```

### Entropy Calculation

For each candidate guess, compute how well it partitions the remaining possibilities:

```python
def calculate_entropy(self, guess: str, word_pool: set[str]) -> float:
    pattern_counts = Counter()
    for answer in word_pool:
        pattern = self.get_pattern(guess, answer)
        pattern_counts[pattern] += 1
    
    total = len(word_pool)
    entropy = -sum((c/total) * log2(c/total) for c in pattern_counts.values())
    return entropy
```

Higher entropy = more even split = more information gained = better guess.

## Output Explained

```
════════════════════════════════════════════════════════════
              TOP RECOMMENDATIONS (ENTROPY MODE)
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
- **Freq.Score**: Word frequency score (bot mode only, higher = more common)
- **Possible?**: Whether this word could be the actual answer

## Recommended Opening Words

| Mode | Word | Score |
|------|------|-------|
| Entropy | SALET | ~6.1 bits |
| Entropy | REAST | ~6.1 bits |
| Entropy | CRATE | ~5.9 bits |
| Bot | SLATE | exp. ~21 remaining |
| Bot | CRANE | exp. ~22 remaining |

## File Structure

```
wordle-solver/
├── wordle_solver.py        # Main solver script
├── words.txt               # Full word list (14,855 words)
├── solutions_with_freq.csv # Curated solutions + frequency (2,315 words)
├── create_solutions_freq.py # Script to regenerate frequency data
├── README.md               # This file
├── requirements.txt        # Dependencies (none required)
└── LICENSE                 # MIT License
```

## API Usage

```python
from wordle_solver import WordleSolver

# Entropy mode (default)
solver = WordleSolver(word_file="words.txt")

# Bot mode
solver = WordleSolver(
    bot_mode=True,
    word_file="words.txt",
    solutions_file="solutions_with_freq.csv"
)

# Apply guesses
solver.apply_guess("crane", "xxxyx")
solver.apply_guess("tonus", "xygxg")

# Get recommendations (entropy mode)
recommendations = solver.get_best_guess(top_n=5, show_progress=False)
for word, entropy, expected, is_possible in recommendations:
    print(f"{word}: entropy={entropy:.3f}, possible={is_possible}")

# Get recommendations (bot mode)
recommendations = solver.get_best_guess_bot(top_n=5, show_progress=False)
for word, expected, freq_score, is_possible in recommendations:
    print(f"{word}: expected={expected:.1f}, freq={freq_score:.3f}")

# Check remaining possibilities
print(f"Remaining: {len(solver.possible_answers)}")

# Reset for new game
solver.reset()
```

## Regenerating Frequency Data

If you want to update the solutions list or frequency data:

```bash
# Download the source files
# - wordle_solutions.txt from cfreshman's gist
# - word_frequencies.txt from norvig.com/ngrams/count_1w.txt

# Run the cross-reference script
python create_solutions_freq.py
```

## Performance

- **First guess**: ~15,000 × 2,315 pattern computations (~1-3 seconds in bot mode)
- **Later guesses**: Much faster as remaining words decrease
- **Memory**: ~2 MB for word lists

## License

MIT License — see [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Some ideas:

- [ ] Precompute opening word scores for faster startup
- [ ] Add multi-step lookahead (computationally expensive but more optimal)
- [ ] Web interface
- [ ] Support for other Wordle variants (6-letter, etc.)

## Acknowledgments

- Algorithm inspired by [3Blue1Brown's Wordle analysis](https://www.youtube.com/watch?v=v68zYyaEmEA)
- Information theory foundations from Claude Shannon
- Solutions list from [cfreshman's gist](https://gist.github.com/cfreshman/a03ef2cba789d8cf00c08f767e0fad7b)
- Word frequency data from [Peter Norvig / Google Ngrams](https://norvig.com/ngrams/)
