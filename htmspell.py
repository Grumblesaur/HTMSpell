import string
import functools
import argparse
import sys
from typing import Self
from bs4 import BeautifulSoup
from pathlib import Path
from enum import IntEnum


class Lookup(IntEnum):
    NotFound = 0
    ExactMatch = 1
    FoundCasefolded = 2
    FoundCapitalized = 3
    FoundAllCaps = 4

    def note(self):
        if self is self.NotFound:
            return "no matching entry"
        if self is self.FoundCasefolded:
            return "matching entry when lowercase"
        if self is self.FoundCapitalized:
            return "matching entry when Capitalized"
        if self is self.FoundAllCaps:
            return "matching entry when ALLCAPS"
        return ""


@functools.total_ordering
class Typo:
    def __init__(self, source_type: str, n: int, problem: str, lookup: Lookup):
        self.source_type = source_type
        self.n = n
        self.problem = problem
        self.problem_type = lookup

    def __repr__(self):
        return f'{self.__class__.__name__}({self.source_type}, {self.n}, {self.problem})'

    def __str__(self):
        return f'{self.source_type}.{self.n}: {self.problem} [note: {self.problem_type.note()}]'

    def _key(self) -> tuple[str, int, str]:
        return self.source_type, self.n, self.problem

    def __hash__(self) -> int:
        return hash(self._key())

    def __eq__(self, other: Self) -> bool:
        if isinstance(other, self.__class__):
            return self._key() == other._key()
        return False

    def __lt__(self, other: Self) -> bool:
        if isinstance(other, self.__class__):
            return self._key() < other._key()
        return NotImplemented


def tokenize(text: str) -> list[str]:
    words = []
    for raw_token in text.split():
        if '—' in raw_token:
            words.extend(filter(None, raw_token.split('—')))
    return [w.strip(string.punctuation) for w in words]


def lines_from(file: Path) -> set[str]:
    with open(file, 'r', encoding='utf-8') as f:
        return set(f.read().splitlines())


class SpellChecker:
    default_words_paths = [Path('/usr/share/dict/words'), Path('/usr/dict/words')]
    default_source_types = {'p', 'address', 'td', 'th'}

    def __init__(self, source_types: set[str] = None, words_path: Path = None, *extra_words_paths: Path):
        self.source_types = source_types or self.default_source_types
        if words_path is None:
            for path in self.default_words_paths:
                if path.exists(follow_symlinks=True):
                    words_path = path
                    break
            else:
                raise FileNotFoundError('no words path found along {paths}. supply one with --dictionary argument.'
                                        .format(paths=', '.join(repr(str(p)) for p in self.default_words_paths)))

        self.words = lines_from(words_path)
        self.extra_words = set()
        for ewp in extra_words_paths:
            self.extra_words |= lines_from(ewp)

    def check_word(self, word: str) -> Lookup:
        if word in self.words or word in self.extra_words:
            return Lookup.ExactMatch
        if (cf := word.casefold()) in self.words or cf in self.extra_words:
            return Lookup.FoundCasefolded
        if (cp := word.capitalize()) in self.words or cp in self.extra_words:
            return Lookup.FoundCapitalized
        if (up := word.upper()) in self.words or up in self.extra_words:
            return Lookup.FoundAllCaps
        return Lookup.NotFound


    def check_spelling(self, html_file: Path) -> list[Typo]:
        with open(html_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')

        typos = []
        for st in self.source_types:
            source_passages = soup.find_all(st)
            for k, sp in enumerate(source_passages, start=1):
                words = tokenize(sp.text)
                for word in words:
                    if (result := self.check_word(word)) != Lookup.ExactMatch:
                        typos.append(Typo(st, k, word, result))
        return typos


def make_argument_parser():
    parser = argparse.ArgumentParser(description="Check spelling of HTML files.")
    parser.add_argument('filenames', nargs='+')
    parser.add_argument('-d', '--dictionary', type=Path, help="path to a dictionary file")
    parser.add_argument('-e', '--extra-words', type=Path, help="path to a user-created dictionary file")
    parser.add_argument('-s', '--source-types', type=str, help="comma-separated list of HTML elements to check")
    return parser


def main():
    parser = make_argument_parser()
    args = parser.parse_args()
    source_types = set(args.source_types.split(','))
    extra_words = args.extra_words
    dictionary = args.dictionary

    sc = SpellChecker(source_types, dictionary, extra_words)

    for filename in args.filenames:
        try:
            typos = sc.check_spelling(filename)
        except FileNotFoundError as e:
            print(e)
        else:
            for t in typos:
                print(str(t))

if __name__ == '__main__':
    main()
