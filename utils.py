import re
import string
from typing import Iterable


def tokenize(text: str) -> Iterable[str]:
    yield from text.split()


def dehyphenate(tokens: Iterable[str], **kwargs) -> Iterable[str]:
    regex_str = r'[—-]' if kwargs.get('dehyphenate') else r'—'
    dash = re.compile(regex_str)
    for token in tokens:
        if dash.search(token):
            yield from (subtoken for subtoken in dash.split(token) if subtoken)
        else:
            yield token


def remove_enclitics(tokens: Iterable[str], **kwargs) -> Iterable[str]:
    if not kwargs.get('ignore_enclitics', False):
        yield from tokens
        return
    if not (enclitics := kwargs.get('enclitics')):
        yield from tokens
        return
    for token in tokens:
        for enc in enclitics:
            if token.endswith(enc):
                yield token.removesuffix(enc)
                break
        else:
            yield token

def ignore_capitalized(tokens: Iterable[str], **kwargs) -> Iterable[str]:
    if not kwargs.get('ignore_capitalized', False):
        yield from tokens
        return
    for token in tokens:
        if token[0].isupper():
            continue
        yield token


def clean(tokens: Iterable[str]) -> Iterable[str]:
    return (t.strip(string.punctuation+' ') for t in tokens)


def parse_selection(s: str) -> list[int]:
    item_numbers = []
    for selection in s.split(','):
        if (n := selection.strip()).isdigit():
            item_numbers.append(int(n))
        else:
            raise TypeError(f"Cannot parse int from {selection!r}")
    return item_numbers


def valid_selection(v: set[int], valid: set[int]) -> bool:
    for x in v:
        if x not in valid:
            raise ValueError(f"No dictionary correspond to {x!r}")
    return True
