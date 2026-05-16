import functools
from enum import StrEnum
from pathlib import Path
from typing import Self

from bs4 import BeautifulSoup

import utils


class EntryMatch(StrEnum):
    NotFound = 'NotFound'
    Exact = 'Exact'
    Casefolded = 'Casefolded'
    Capitalized = 'Capitalized'
    AllCaps = 'AllCaps'

    def note(self):
        if self is self.NotFound:
            return "no matching entry"
        if self is self.Casefolded:
            return "matching entry when lowercase"
        if self is self.Capitalized:
            return "matching entry when Capitalized"
        if self is self.AllCaps:
            return "matching entry when ALLCAPS"
        return ""

    @classmethod
    def from_string(cls, option: str) -> EntryMatch:
        if option.casefold() == 'notfound':
            return cls.NotFound
        if option.casefold() == 'exact':
            return cls.Exact
        if option.casefold() == 'casefolded':
            return cls.Casefolded
        if option.casefold() == 'capitalized':
            return cls.Capitalized
        if option.casefold() == 'allcaps':
            return cls.AllCaps
        raise ValueError(f'unrecognized string: {option}')

    @classmethod
    def parse_problems(cls, problems: str) -> set[EntryMatch]:
        return {cls.from_string(p) for p in problems.split(',')}

@functools.total_ordering
class Typo:
    def __init__(self, source_type: str, n: int, problem: str, lookup: EntryMatch):
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
            # noinspection PyTypeChecker
            return self._key() < other._key()
        return NotImplemented


def lines_from(file: Path) -> set[str]:
    with open(file, 'r', encoding='utf-8') as f:
        return set(f.read().splitlines())


class SpellChecker:
    default_problems = {EntryMatch.NotFound, EntryMatch.Capitalized, EntryMatch.AllCaps}

    def __init__(self, word_sources: set[Path], elements: set[str], problems: set[EntryMatch] = None):
        self.elements = elements
        self.words = set()
        self.problems = problems or self.default_problems
        for ws in word_sources:
            self.words.update(lines_from(ws))

    def check_word(self, word: str) -> EntryMatch:
        """Return a result of type EntryMatch based on `word`'s presence
        (or absence) in our dictionaries."""
        if word in self.words:
            return EntryMatch.Exact
        if word.casefold() in self.words:
            return EntryMatch.Casefolded
        if word.capitalize() in self.words:
            return EntryMatch.Capitalized
        if word.upper() in self.words:
            return EntryMatch.AllCaps
        return EntryMatch.NotFound


    def check_spelling(self, html_file: Path, **options) -> list[Typo]:
        with open(html_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')

        typos = []
        for st in self.elements:
            source_passages = soup.find_all(st)
            for k, sp in enumerate(source_passages, start=1):
                words = utils.tokenize(sp.text)
                dehyphenated = utils.dehyphenate(words, **options)
                caps_filtered = utils.ignore_capitalized(dehyphenated, **options)
                deencliticized = utils.remove_enclitics(caps_filtered, **options)
                cleaned = utils.clean(deencliticized)
                for word in filter(bool, cleaned):
                    if (result := self.check_word(word)) in self.problems:
                        typos.append(Typo(st, k, word, result))
        return typos
