#!/usr/bin/env python3
"""
Wordle Solver - Optimal Information-Theoretic Approach
=======================================================

Uses entropy maximization to find the optimal next guess.
The algorithm calculates expected information gain for each candidate word,
selecting the word that best partitions the remaining solution space.

Usage:
    python wordle_solver.py

Input format for clues:
    - 'g' = Green (correct position)
    - 'y' = Yellow (wrong position)  
    - 'x' = Gray (not in word)
    
Example: If you guessed "CRANE" and got ⬛🟨🟩⬛🟩, enter: xygxg
"""

import math
from collections import Counter
from typing import Optional

# =============================================================================
# WORD LIST CONFIGURATION
# =============================================================================

import os
import csv

# Path to external word list file (one word per line)
# Will search in: current directory, script directory, or absolute path
WORD_LIST_FILE = "words.txt"

# Path to solutions with frequency file for bot mode (CSV: word,frequency)
SOLUTIONS_FREQ_FILE = "solutions_with_freq.csv"

# Fallback words if file not found (minimal set for emergencies)
FALLBACK_WORDS = """
about crane slate trace audio adieu raise arose salet reast stare snare irate
later alert alter laser saner nears learn renal liner riles tiles stile smile
miles limes slime motes tomes notes tones stone onset pores spore ropes store
""".split()


class WordleSolver:
    """
    Optimal Wordle Solver using Information Theory (Entropy Maximization).
    
    Modes:
    - Default: Entropy maximization over all words (mathematically optimal)
    - Bot mode: Mimics NYT Wordle Bot with curated solutions list + frequency weighting
    - Hard mode: Only suggests words that could be the answer
    
    The algorithm:
    1. Maintains a pool of possible solutions
    2. For each candidate guess, computes expected information gain (entropy)
       or expected remaining solutions (bot mode)
    3. Selects the optimal guess based on the scoring method
    """
    
    def __init__(self, hard_mode: bool = False, word_file: str = None, 
                 bot_mode: bool = False, solutions_file: str = None):
        self.hard_mode = hard_mode
        self.bot_mode = bot_mode
        
        # Load main word list (valid guesses)
        self.all_words = self._load_words(word_file)
        
        # Bot mode: load curated solutions with frequencies
        if bot_mode:
            self.solutions_list, self.word_frequencies = self._load_solutions_with_freq(solutions_file)
            if self.solutions_list:
                self.possible_answers = set(self.solutions_list)
                print(f"🤖 BOT MODE: Using {len(self.solutions_list)} curated solutions")
            else:
                print("⚠ Bot mode requested but solutions file not found. Using standard mode.")
                self.bot_mode = False
                self.possible_answers = set(self.all_words)
                self.word_frequencies = {}
        else:
            self.possible_answers = set(self.all_words)
            self.word_frequencies = {}
            self.solutions_list = []
        
        self.guesses_made: list[tuple[str, str]] = []
        self.letter_freq = self._compute_letter_frequencies()
    
    def _load_solutions_with_freq(self, solutions_file: str = None) -> tuple[list[str], dict[str, int]]:
        """
        Load curated solutions list with frequency data for bot mode.
        
        Returns: (list of solution words, dict of word -> frequency)
        """
        file_to_use = solutions_file or SOLUTIONS_FREQ_FILE
        
        search_paths = [
            file_to_use,
            os.path.join(os.path.dirname(os.path.abspath(__file__)), file_to_use),
        ]
        
        for path in search_paths:
            if os.path.exists(path):
                try:
                    solutions = []
                    frequencies = {}
                    with open(path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            word = row['word'].lower().strip()
                            freq = int(row.get('frequency', 1))
                            if len(word) == 5 and word.isalpha():
                                solutions.append(word)
                                frequencies[word] = freq
                    if solutions:
                        print(f"✓ Loaded {len(solutions)} solutions with frequencies from: {path}")
                        return solutions, frequencies
                except Exception as e:
                    print(f"⚠ Error reading {path}: {e}")
        
        return [], {}
        
    def _load_words(self, word_file: str = None) -> list[str]:
        """
        Load words from external file, with fallback to built-in list.
        
        Search order for word file:
        1. Explicit path provided
        2. Current working directory
        3. Same directory as script
        """
        file_to_use = word_file or WORD_LIST_FILE
        
        # Try multiple locations
        search_paths = [
            file_to_use,  # As provided / current directory
            os.path.join(os.path.dirname(os.path.abspath(__file__)), file_to_use),  # Script directory
        ]
        
        for path in search_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        words = [line.strip().lower() for line in f]
                    words = [w for w in words if len(w) == 5 and w.isalpha()]
                    words = list(set(words))
                    if words:
                        print(f"✓ Loaded {len(words)} words from: {path}")
                        return sorted(words)
                except Exception as e:
                    print(f"⚠ Error reading {path}: {e}")
        
        # Fallback to built-in words
        print(f"⚠ Word file '{file_to_use}' not found. Using fallback list ({len(FALLBACK_WORDS)} words).")
        print(f"  Place 'words.txt' in the same folder as this script for best results.")
        words = [w.strip().lower() for w in FALLBACK_WORDS if len(w.strip()) == 5]
        return sorted(set(w for w in words if w.isalpha()))
    
    def _compute_letter_frequencies(self) -> dict[str, float]:
        """Compute letter frequencies for tiebreaking."""
        freq: Counter = Counter()
        for word in self.all_words:
            freq.update(set(word))
        total = sum(freq.values())
        return {letter: count / total for letter, count in freq.items()}
    
    @staticmethod
    def get_pattern(guess: str, answer: str) -> str:
        """
        Compute Wordle feedback pattern.
        
        Returns: 'g' = green, 'y' = yellow, 'x' = gray
        """
        pattern = ['x'] * 5
        answer_chars = list(answer)
        
        # First pass: mark greens (correct position)
        for i, (g, a) in enumerate(zip(guess, answer)):
            if g == a:
                pattern[i] = 'g'
                answer_chars[i] = None
        
        # Second pass: mark yellows (wrong position)
        for i, g in enumerate(guess):
            if pattern[i] == 'x' and g in answer_chars:
                pattern[i] = 'y'
                answer_chars[answer_chars.index(g)] = None
                
        return ''.join(pattern)
    
    def filter_words(self, guess: str, pattern: str, word_pool: set[str]) -> set[str]:
        """Filter words based on guess and feedback pattern."""
        return {
            word for word in word_pool
            if self.get_pattern(guess, word) == pattern
        }
    
    def apply_guess(self, guess: str, pattern: str) -> int:
        """
        Apply a guess and its feedback to narrow down possibilities.
        
        Returns: Number of remaining possible answers
        """
        guess = guess.lower().strip()
        pattern = pattern.lower().strip()
        
        if len(guess) != 5 or not guess.isalpha():
            raise ValueError("Guess must be exactly 5 letters")
        if len(pattern) != 5 or not all(c in 'gyx' for c in pattern):
            raise ValueError("Pattern must be 5 characters of g/y/x")
        
        self.guesses_made.append((guess, pattern))
        self.possible_answers = self.filter_words(guess, pattern, self.possible_answers)
        
        return len(self.possible_answers)
    
    def calculate_entropy(self, guess: str, word_pool: set[str]) -> float:
        """
        Calculate expected information gain (entropy) for a guess.
        
        Higher entropy = better guess (eliminates more possibilities on average)
        """
        if not word_pool:
            return 0.0
            
        pattern_counts: Counter = Counter()
        for answer in word_pool:
            pattern = self.get_pattern(guess, answer)
            pattern_counts[pattern] += 1
        
        total = len(word_pool)
        entropy = 0.0
        for count in pattern_counts.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)
                
        return entropy
    
    def calculate_expected_remaining(self, guess: str, word_pool: set[str]) -> float:
        """
        Calculate expected number of remaining words after this guess.
        Lower = better
        """
        if not word_pool:
            return 0.0
            
        pattern_counts: Counter = Counter()
        for answer in word_pool:
            pattern = self.get_pattern(guess, answer)
            pattern_counts[pattern] += 1
        
        total = len(word_pool)
        return sum(count * count for count in pattern_counts.values()) / total
    
    def get_word_score(self, word: str) -> float:
        """
        Tiebreaker score for ranking words with similar entropy/expected values.
        
        In bot mode: uses word frequency (higher = more common = preferred)
        In normal mode: uses letter frequencies
        """
        if self.bot_mode and word in self.word_frequencies:
            # Normalize frequency to 0-1 range using log scale
            freq = self.word_frequencies[word]
            return math.log10(freq + 1) / 10  # Scaled log frequency
        return sum(self.letter_freq.get(c, 0) for c in set(word))
    
    def get_best_guess_bot(self, top_n: int = 10, show_progress: bool = True) -> list[tuple[str, float, float, bool]]:
        """
        Find optimal guesses using bot-style scoring (minimize expected remaining).
        
        This mimics NYT Wordle Bot behavior:
        - Minimize expected remaining solutions
        - Use word frequency as tiebreaker
        - Prefer words that could be answers
        
        Returns: List of (word, expected_remaining, frequency_score, is_possible_answer) tuples
        """
        if not self.possible_answers:
            return []
        
        if len(self.possible_answers) == 1:
            word = list(self.possible_answers)[0]
            return [(word, 1.0, self.get_word_score(word), True)]
        
        if len(self.possible_answers) == 2:
            results = []
            for word in self.possible_answers:
                results.append((word, 1.0, self.get_word_score(word), True))
            results.sort(key=lambda x: -x[2])  # Sort by frequency
            return results
        
        # Determine candidate pool
        if self.hard_mode:
            candidates = self.possible_answers
        else:
            # Consider all valid guesses
            candidates = set(self.all_words)
        
        results = []
        total = len(candidates)
        
        for i, word in enumerate(candidates):
            if show_progress and i % 500 == 0:
                print(f"\r   Analyzing: {i}/{total} words...", end="", flush=True)
            
            expected = self.calculate_expected_remaining(word, self.possible_answers)
            freq_score = self.get_word_score(word)
            is_possible = word in self.possible_answers
            
            results.append((word, expected, freq_score, is_possible))
        
        if show_progress:
            print("\r" + " " * 50 + "\r", end="")
        
        # Sort by: expected remaining (asc), prefer possible answers, frequency (desc)
        results.sort(key=lambda x: (x[1], -x[3], -x[2]))
        
        return results[:top_n]
    
    def get_best_guess(self, top_n: int = 10, show_progress: bool = True) -> list[tuple[str, float, float, bool]]:
        """
        Find the optimal next guess(es) using entropy maximization.
        
        Returns: List of (word, entropy, expected_remaining, is_possible_answer) tuples
        """
        if not self.possible_answers:
            return []
        
        if len(self.possible_answers) == 1:
            word = list(self.possible_answers)[0]
            return [(word, 0.0, 1.0, True)]
        
        if len(self.possible_answers) == 2:
            return [(word, 1.0, 1.0, True) for word in self.possible_answers]
        
        # Determine candidate pool
        candidates = self.possible_answers if self.hard_mode else set(self.all_words)
        
        results = []
        total = len(candidates)
        
        for i, word in enumerate(candidates):
            if show_progress and i % 500 == 0:
                print(f"\r   Analyzing: {i}/{total} words...", end="", flush=True)
            
            entropy = self.calculate_entropy(word, self.possible_answers)
            expected = self.calculate_expected_remaining(word, self.possible_answers)
            is_possible = word in self.possible_answers
            
            results.append((word, entropy, expected, is_possible))
        
        if show_progress:
            print("\r" + " " * 50 + "\r", end="")
        
        # Sort: entropy (desc), prefer possible answers, lower expected, letter freq
        results.sort(key=lambda x: (-x[1], -x[3], x[2], -self.get_word_score(x[0])))
        
        return results[:top_n]
    
    def get_remaining_words(self, max_show: int = 20) -> list[str]:
        """Get list of remaining possible answers."""
        return sorted(self.possible_answers)[:max_show]
    
    def reset(self):
        """Reset the solver to initial state."""
        if self.bot_mode and self.solutions_list:
            self.possible_answers = set(self.solutions_list)
        else:
            self.possible_answers = set(self.all_words)
        self.guesses_made = []


def format_pattern_visual(pattern: str) -> str:
    """Convert pattern string to emoji visualization."""
    emoji_map = {'g': '🟩', 'y': '🟨', 'x': '⬛'}
    return ''.join(emoji_map.get(c, c) for c in pattern)


def print_header():
    """Print the program header."""
    print("\n" + "═" * 60)
    print("          🟩 WORDLE SOLVER - Optimal Strategy 🟩")
    print("═" * 60)
    print("\nUsing ENTROPY MAXIMIZATION for mathematically optimal guesses.\n")
    print("Pattern codes:  g = 🟩 Green   y = 🟨 Yellow   x = ⬛ Gray")
    print("─" * 60)


def print_recommendations(solver: WordleSolver):
    """Print the recommended guesses."""
    print("\n🔍 Calculating optimal guesses...")
    
    # Use different scoring method based on mode
    if solver.bot_mode:
        recommendations = solver.get_best_guess_bot(top_n=10)
        score_label = "Exp.Left"
        mode_label = "🤖 BOT MODE"
    else:
        recommendations = solver.get_best_guess(top_n=10)
        score_label = "Entropy"
        mode_label = "ENTROPY MODE"
    
    if not recommendations:
        print("\n❌ No valid words remaining! Check your inputs.")
        return
    
    # Separate into possible answers and strategic-only guesses
    possible_recs = [(w, e, x, p) for w, e, x, p in recommendations if p]
    strategic_recs = [(w, e, x, p) for w, e, x, p in recommendations if not p]
    
    print("\n" + "═" * 60)
    print(f"              TOP RECOMMENDATIONS ({mode_label})")
    print("═" * 60)
    
    if solver.bot_mode:
        print(f"{'Rank':<5} {'Word':<10} {'Exp.Left':<10} {'Freq.Score':<10} {'Possible?'}")
    else:
        print(f"{'Rank':<5} {'Word':<10} {'Entropy':<10} {'Exp.Left':<10} {'Possible?'}")
    print("─" * 60)
    
    for i, (word, score1, score2, is_possible) in enumerate(recommendations, 1):
        possible_str = "✓ Yes" if is_possible else "  No"
        if solver.bot_mode:
            print(f"{i:<5} {word.upper():<10} {score1:<10.1f} {score2:<10.3f} {possible_str}")
        else:
            print(f"{i:<5} {word.upper():<10} {score1:<10.3f} {score2:<10.1f} {possible_str}")
    
    print("─" * 60)
    
    # If there are strategic guesses in top 10, show a separate "best possible answers" table
    total_remaining = len(solver.possible_answers)
    
    if strategic_recs and total_remaining > 2:
        # Get top 5 among possible answers only
        if solver.bot_mode:
            all_possible_ranked = sorted(
                [(w, solver.calculate_expected_remaining(w, solver.possible_answers),
                  solver.get_word_score(w), True)
                 for w in solver.possible_answers],
                key=lambda x: (x[1], -x[2])
            )[:5]
            
            print("\n" + "─" * 60)
            print("         TOP POSSIBLE ANSWERS (if you must guess one)")
            print("─" * 60)
            print(f"{'Rank':<5} {'Word':<10} {'Exp.Left':<10} {'Freq.Score':<10}")
            print("─" * 60)
            
            for i, (word, expected, freq, _) in enumerate(all_possible_ranked, 1):
                print(f"{i:<5} {word.upper():<10} {expected:<10.1f} {freq:<10.3f}")
        else:
            all_possible_ranked = sorted(
                [(w, solver.calculate_entropy(w, solver.possible_answers),
                  solver.calculate_expected_remaining(w, solver.possible_answers), True)
                 for w in solver.possible_answers],
                key=lambda x: (-x[1], x[2])
            )[:5]
            
            print("\n" + "─" * 60)
            print("         TOP POSSIBLE ANSWERS (if you must guess one)")
            print("─" * 60)
            print(f"{'Rank':<5} {'Word':<10} {'Entropy':<10} {'Exp.Left':<10}")
            print("─" * 60)
            
            for i, (word, entropy, expected, _) in enumerate(all_possible_ranked, 1):
                print(f"{i:<5} {word.upper():<10} {entropy:<10.3f} {expected:<10.1f}")
        
        print("─" * 60)
    
    # Show remaining words if few enough
    print(f"\n📊 Remaining possible answers: {total_remaining}")
    if total_remaining <= 20:
        # Sort by score (best first)
        if solver.bot_mode:
            ranked_remaining = sorted(
                solver.possible_answers,
                key=lambda w: (solver.calculate_expected_remaining(w, solver.possible_answers), 
                              -solver.get_word_score(w))
            )
            print("   (sorted by expected remaining, then frequency)")
        else:
            ranked_remaining = sorted(
                solver.possible_answers,
                key=lambda w: -solver.calculate_entropy(w, solver.possible_answers)
            )
            print("   (sorted by entropy, best first)")
        print("   " + ", ".join(w.upper() for w in ranked_remaining))
    elif total_remaining <= 50:
        remaining = solver.get_remaining_words(max_show=15)
        print("   " + ", ".join(w.upper() for w in remaining) + "...")
    
    print()


def print_guess_history(solver: WordleSolver):
    """Print the history of guesses made."""
    if not solver.guesses_made:
        print("\n   No guesses made yet.")
        return
    
    print("\n   Guess History:")
    for i, (word, pattern) in enumerate(solver.guesses_made, 1):
        print(f"   {i}. {word.upper()} → {format_pattern_visual(pattern)}")
    print()


def interactive_mode(word_file: str = None, hard_mode: bool = False, 
                     bot_mode: bool = False, solutions_file: str = None):
    """Run the solver in interactive mode."""
    print_header()
    
    solver = WordleSolver(hard_mode=hard_mode, word_file=word_file,
                          bot_mode=bot_mode, solutions_file=solutions_file)
    
    if bot_mode and solver.bot_mode:
        print("\n🤖 BOT MODE ACTIVE: Mimics NYT Wordle Bot scoring")
        print("   • Uses curated ~2,300 word solutions list")
        print("   • Minimizes expected remaining solutions")
        print("   • Prefers common words as tiebreaker")
    
    if hard_mode:
        print("\n⚠️  HARD MODE: Only possible answers will be suggested.")
    
    # Suggest opening words
    print("\n🎯 RECOMMENDED OPENING WORDS (highest average entropy):")
    print("   SALET, REAST, CRATE, TRACE, SLATE, CRANE, AROSE")
    print("\n💡 Commands: /hint = get recommendations, /history = show guesses")
    print("             /reset = start over, /quit = exit")
    
    guess_num = 1
    
    while True:
        print("\n" + "─" * 60)
        print(f"\n📝 GUESS #{guess_num}")
        
        word = input("   Enter your guess: ").strip().lower()
        
        # Commands use / prefix to avoid collision with valid words like "reset"
        if word in ('/quit', '/q'):
            print("\nThanks for using Wordle Solver! Good luck! 🍀\n")
            break
        
        if word in ('/reset', '/r'):
            solver.reset()
            guess_num = 1
            print("\n🔄 Solver reset! Starting fresh.\n")
            continue
        
        if word in ('/hint', '/h'):
            print_recommendations(solver)
            continue
        
        if word in ('/history', '/hi'):
            print_guess_history(solver)
            continue
        
        if word.startswith('/'):
            print("   ⚠️  Unknown command. Available: /hint, /history, /reset, /quit")
            continue
        
        if len(word) != 5 or not word.isalpha():
            print("   ⚠️  Please enter a valid 5-letter word.")
            continue
        
        pattern = input("   Enter the pattern (g/y/x): ").strip().lower()
        
        if len(pattern) != 5 or not all(c in 'gyx' for c in pattern):
            print("   ⚠️  Pattern must be 5 characters using only g, y, x.")
            print("   Example: If you got ⬛🟨🟩⬛🟩, enter: xygxg")
            continue
        
        # Show visual feedback
        print(f"   Result: {word.upper()} → {format_pattern_visual(pattern)}")
        
        # Check for win
        if pattern == 'ggggg':
            print(f"\n🎉 CONGRATULATIONS! You solved it in {guess_num} guess{'es' if guess_num > 1 else ''}!")
            print(f"   The answer was: {word.upper()}\n")
            
            again = input("Play again? (y/n): ").strip().lower()
            if again == 'y':
                solver.reset()
                guess_num = 1
                print("\n🔄 Starting new game!\n")
                continue
            else:
                print("\nThanks for playing! 🍀\n")
                break
        
        # Apply guess and show recommendations
        try:
            remaining = solver.apply_guess(word, pattern)
            guess_num += 1
            
            if remaining == 0:
                print("\n❌ No valid words remaining! This might indicate:")
                print("   • A typo in your guess or pattern")
                print("   • The answer isn't in our word list")
                print("   Use 'reset' to start over.\n")
            elif remaining == 1:
                answer = list(solver.possible_answers)[0]
                print(f"\n🎯 THE ANSWER MUST BE: {answer.upper()}")
                print("   (Only one possibility remaining!)\n")
            else:
                print_recommendations(solver)
                
        except ValueError as e:
            print(f"   ⚠️  Error: {e}")


def batch_solve(guesses: list[tuple[str, str]], verbose: bool = True) -> Optional[str]:
    """
    Solve with predefined guesses (for programmatic use).
    
    Args:
        guesses: List of (word, pattern) tuples
        verbose: Whether to print progress
        
    Returns:
        Best next guess, or the answer if only one remains
    """
    solver = WordleSolver()
    
    for word, pattern in guesses:
        solver.apply_guess(word, pattern)
        if verbose:
            remaining = len(solver.possible_answers)
            print(f"After {word.upper()}: {remaining} words remaining")
    
    if len(solver.possible_answers) == 0:
        return None
    elif len(solver.possible_answers) == 1:
        answer = list(solver.possible_answers)[0]
        if verbose:
            print(f"\n✓ Answer: {answer.upper()}")
        return answer
    else:
        recommendations = solver.get_best_guess(top_n=5, show_progress=verbose)
        if verbose:
            print("\nTop recommendations:")
            for word, entropy, expected, is_poss in recommendations:
                status = "✓" if is_poss else " "
                print(f"  {status} {word.upper()}: entropy={entropy:.3f}")
        return recommendations[0][0] if recommendations else None


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Optimal Wordle Solver using entropy maximization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Interactive mode:
    python wordle_solver.py
    
  Bot mode (mimics NYT Wordle Bot):
    python wordle_solver.py --bot
    
  Batch mode with guesses:
    python wordle_solver.py "crane:xygxg" "spilt:gxxxx"
    
  Use custom word list:
    python wordle_solver.py -w mywords.txt "crane:xxxyx"
    
  Bot mode with custom solutions file:
    python wordle_solver.py --bot -s my_solutions.csv
    
Pattern format: g=green, y=yellow, x=gray
        """
    )
    parser.add_argument("guesses", nargs="*", help="Guesses in 'word:pattern' format")
    parser.add_argument("-w", "--wordlist", default=None, help="Path to word list file")
    parser.add_argument("-s", "--solutions", default=None, help="Path to solutions+frequency CSV (for bot mode)")
    parser.add_argument("--hard", action="store_true", help="Hard mode (only suggest possible answers)")
    parser.add_argument("--bot", action="store_true", help="Bot mode (mimic NYT Wordle Bot with curated solutions)")
    
    args = parser.parse_args()
    
    if args.guesses:
        # Batch mode
        guesses = []
        for arg in args.guesses:
            if ':' in arg:
                word, pattern = arg.split(':')
                guesses.append((word.strip(), pattern.strip()))
        
        if guesses:
            mode_str = "Bot Mode" if args.bot else "Batch Mode"
            print("\n" + "═" * 40)
            print(f"  WORDLE SOLVER - {mode_str}")
            print("═" * 40 + "\n")
            
            solver = WordleSolver(
                hard_mode=args.hard, 
                word_file=args.wordlist,
                bot_mode=args.bot,
                solutions_file=args.solutions
            )
            
            for word, pattern in guesses:
                solver.apply_guess(word, pattern)
                remaining = len(solver.possible_answers)
                print(f"After {word.upper()}: {remaining} words remaining")
            
            if len(solver.possible_answers) == 0:
                print("\n✗ No valid words remaining!")
            elif len(solver.possible_answers) == 1:
                answer = list(solver.possible_answers)[0]
                print(f"\n✓ Answer: {answer.upper()}")
            else:
                if args.bot:
                    recs = solver.get_best_guess_bot(top_n=5, show_progress=True)
                    print("\nTop recommendations (Bot Mode - by expected remaining):")
                    for word, expected, freq, is_poss in recs:
                        status = "✓" if is_poss else " "
                        print(f"  {status} {word.upper()}: exp={expected:.1f}, freq={freq:.3f}")
                else:
                    recs = solver.get_best_guess(top_n=5, show_progress=True)
                    print("\nTop recommendations:")
                    for word, entropy, expected, is_poss in recs:
                        status = "✓" if is_poss else " "
                        print(f"  {status} {word.upper()}: entropy={entropy:.3f}")
        else:
            parser.print_help()
    else:
        # Interactive mode
        interactive_mode(
            word_file=args.wordlist, 
            hard_mode=args.hard,
            bot_mode=args.bot,
            solutions_file=args.solutions
        )
