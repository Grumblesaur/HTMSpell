import functools
import re
import string
from enum import IntEnum
from pathlib import Path
from typing import Self, Iterable

from bs4 import BeautifulSoup


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
        return f'{self.source_type}.{self.n}: {self.problem} [{self.problem_type.note()}]'

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


def tokenize(text: str, **kwargs) -> list[str]:
    words = []
    dash = re.compile('[—-]') if kwargs.get('dehyphenate') else re.compile('—')
    for raw_token in text.split():
        if dash.search(raw_token):
            for subtoken in dash.split(raw_token):
                if subtoken.strip():
                    words.append(subtoken)
        else:
            words.append(raw_token)

    cleaned = []
    enclitics = kwargs.get('enclitics', [])
    for word in words:
        if not (cleaned_word := word.strip(string.punctuation)):
            continue
        for enc in enclitics:
            if word.endswith(enc):
                word.removesuffix(enc)
                break
    return cleaned


def lines_from(file: Path) -> set[str]:
    with open(file, 'r', encoding='utf-8') as f:
        return set(f.read().splitlines())


class SpellChecker:
    problems = {Lookup.NotFound, Lookup.FoundCapitalized, Lookup.FoundAllCaps}

    def __init__(self, word_sources: Iterable[Path], elements: set[str]):
        self.elements = elements
        self.words = set()
        for ws in word_sources:
            self.words.update(lines_from(ws))

    def check_word(self, word: str) -> Lookup:
        if word in self.words or word:
            return Lookup.ExactMatch
        if word.casefold() in self.words:
            return Lookup.FoundCasefolded
        if word.capitalize() in self.words:
            return Lookup.FoundCapitalized
        if word.upper() in self.words:
            return Lookup.FoundAllCaps
        return Lookup.NotFound


    def check_spelling(self, html_file: Path, **options) -> list[Typo]:
        with open(html_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')

        typos = []
        for st in self.elements:
            source_passages = soup.find_all(st)
            for k, sp in enumerate(source_passages, start=1):
                words = tokenize(sp.text, **options)
                for word in words:
                    if (result := self.check_word(word)) in self.problems:
                        typos.append(Typo(st, k, word, result))
        return typos
