import utils
from pathlib import Path
from bs4 import BeautifulSoup, Tag
from typing import Iterable
from collections import Counter

def ilen(v: Iterable) -> int:
    return sum(1 for _ in v)


class DOM:
    Paired = {
        '[': ']',
        '(': ')',
        '{': '}',
        "“": "”",
        '‘': '’'
    }
    PairedReverse = {v: k for k, v in Paired.items()}

    def __init__(self, html_file: Path):
        with open(html_file, 'r', encoding='utf-8') as f:
            self.soup = BeautifulSoup(f, 'html.parser')

    def count_words(self, **options) -> int:
        body = self.soup.find('body')
        return ilen(utils.dehyphenate(utils.tokenize(body.text), **options))

    def count_elements(self, elements: set[str] = None) -> Counter[str]:
        elements = elements or {'p'}
        c = Counter()
        for e in elements:
            for _ in self.soup.find_all(e):
                c[e] += 1
        return c

    def unpaired_characters(self, elements: set[str] = None):
        elements = elements or {'p'}
        stack = []
        errors = []
        for element in elements:
            for n, e in enumerate(self.soup.find_all(element), start=1):
                for c in e.text:
                    if c in self.Paired.keys():
                        stack.append(c)
                    if c in self.PairedReverse.keys():
                        try:
                            popped = stack.pop()
                        except IndexError:
                            errors.append((element, n, c))
                        else:
                            if popped != self.PairedReverse[c]:
                                errors.append((element, n, c))
                char_counts = Counter(e.text)
                if char_counts['"'] % 2:
                    print(e)
                    errors.append((element, n, '"'))
        return errors

    def get(self, element_type: str, index: int) -> Tag:
        elist = self.soup.find_all(element_type)
        try:
            return elist[index - 1]
        except IndexError:
            if not elist:
                raise IndexError(f"no elements of type `{element_type}")
            if index < 1:
                raise IndexError(f'invalid index: {index}; must be 1 or greater')
            raise IndexError(f'attempted to index {element_type}.{index},'
                             + f' but only {len(elist)} `{element_type}`s are present')


