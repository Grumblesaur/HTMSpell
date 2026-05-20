import pyperclip
import sys
import argparse
from pathlib import Path
from bs4 import BeautifulSoup


def make_argument_parser():
    parser = argparse.ArgumentParser(prog=sys.argv[0],
                                     description="Captures the inner HTML of a DOM's `body` element.")
    parser.add_argument('filename', help="The HTML file to yank from.", type=Path)
    parser.add_argument('-e', '--element',
                        type=str,
                        default="body",
                        help="The element type to yank from, the `-n`th of which will be yanked.")
    parser.add_argument('-n', '--index',
                        type=int,
                        default=1,
                        help="Which in a series (1-indexed) of elements to yank.")
    return parser


def main():
    namespace = make_argument_parser().parse_args()
    with open(namespace.filename, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    elements = soup.find_all(namespace.element)
    if namespace.index < 1:
        raise ValueError(f'value of `-n/--index` must be greater than or equal to 1.')
    element = elements[namespace.index - 1]
    subelements = [str(ch).strip() for ch in element.children]
    pyperclip.copy('\n'.join(subelements))


if __name__ == '__main__':
    main()



