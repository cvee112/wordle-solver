#!/usr/bin/env python3
"""
Cross-reference Wordle solutions with word frequency data.

This script:
1. Loads the official Wordle solutions list (~2,314 words)
2. Cross-references with Peter Norvig's word frequency data (Google corpus)
3. Outputs a combined file: solutions_with_freq.csv

Usage:
    python create_solutions_freq.py

Input files (expected in same directory or specify paths):
    - wordle_solutions.txt: One word per line
    - word_frequencies.txt: Format "word\tfrequency" per line

Output:
    - solutions_with_freq.csv: word,frequency (sorted by frequency desc)
"""

import os
import sys
from pathlib import Path


def load_solutions(filepath: str) -> list[str]:
    """Load wordle solutions list."""
    with open(filepath, 'r', encoding='utf-8') as f:
        words = [line.strip().lower() for line in f if line.strip()]
    return [w for w in words if len(w) == 5 and w.isalpha()]


def load_frequencies(filepath: str) -> dict[str, int]:
    """Load word frequency data (word<tab>count format)."""
    freq = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 2:
                word = parts[0].lower()
                try:
                    count = int(parts[1])
                    freq[word] = count
                except ValueError:
                    continue
    return freq


def create_solutions_with_freq(
    solutions_file: str,
    freq_file: str,
    output_file: str,
    default_freq: int = 1
) -> dict:
    """
    Cross-reference solutions with frequencies and save to CSV.
    
    Returns statistics about the merge.
    """
    print(f"Loading solutions from: {solutions_file}")
    solutions = load_solutions(solutions_file)
    print(f"  → Loaded {len(solutions)} solution words")
    
    print(f"\nLoading frequencies from: {freq_file}")
    frequencies = load_frequencies(freq_file)
    print(f"  → Loaded {len(frequencies)} word frequencies")
    
    # Cross-reference
    print("\nCross-referencing...")
    results = []
    found = 0
    not_found = []
    
    for word in solutions:
        if word in frequencies:
            results.append((word, frequencies[word]))
            found += 1
        else:
            results.append((word, default_freq))
            not_found.append(word)
    
    # Sort by frequency (descending)
    results.sort(key=lambda x: -x[1])
    
    # Save to CSV
    print(f"\nSaving to: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("word,frequency\n")
        for word, freq in results:
            f.write(f"{word},{freq}\n")
    
    # Statistics
    stats = {
        'total_solutions': len(solutions),
        'found_in_freq': found,
        'not_found': len(not_found),
        'not_found_words': not_found[:20],  # First 20 for display
        'max_freq': results[0] if results else None,
        'min_freq': results[-1] if results else None,
    }
    
    return stats


def main():
    # Default file paths
    script_dir = Path(__file__).parent
    
    solutions_file = script_dir / "wordle_solutions.txt"
    freq_file = script_dir / "word_frequencies.txt"
    output_file = script_dir / "solutions_with_freq.csv"
    
    # Check for command line overrides
    if len(sys.argv) >= 3:
        solutions_file = Path(sys.argv[1])
        freq_file = Path(sys.argv[2])
    if len(sys.argv) >= 4:
        output_file = Path(sys.argv[3])
    
    # Validate inputs exist
    if not solutions_file.exists():
        print(f"Error: Solutions file not found: {solutions_file}")
        sys.exit(1)
    if not freq_file.exists():
        print(f"Error: Frequency file not found: {freq_file}")
        sys.exit(1)
    
    print("=" * 60)
    print("  Wordle Solutions + Frequency Cross-Reference Tool")
    print("=" * 60)
    
    stats = create_solutions_with_freq(
        str(solutions_file),
        str(freq_file),
        str(output_file)
    )
    
    print("\n" + "=" * 60)
    print("  RESULTS")
    print("=" * 60)
    print(f"  Total solutions:     {stats['total_solutions']}")
    print(f"  Found in freq data:  {stats['found_in_freq']} ({100*stats['found_in_freq']/stats['total_solutions']:.1f}%)")
    print(f"  Not found:           {stats['not_found']}")
    
    if stats['max_freq']:
        print(f"\n  Most common:  {stats['max_freq'][0].upper()} (freq: {stats['max_freq'][1]:,})")
    if stats['min_freq']:
        print(f"  Least common: {stats['min_freq'][0].upper()} (freq: {stats['min_freq'][1]:,})")
    
    if stats['not_found_words']:
        print(f"\n  Sample words not in frequency data:")
        print(f"    {', '.join(stats['not_found_words'][:10])}")
    
    print("\n" + "=" * 60)
    print(f"  ✓ Output saved to: {output_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()
