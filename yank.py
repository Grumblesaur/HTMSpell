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
    parser.add_argument('-v', '--verbose',
                        action="store_true",
                        help="Print the yanked selection to stdout.")
    parser.add_argument('-x', '--no-copy',
                        action="store_true",
                        help="Don't copy the yanked selection to clipboard.")
    return parser


def main():
    namespace = make_argument_parser().parse_args()
    with open(namespace.filename, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    elements = soup.find_all(namespace.element)
    if namespace.index < 1:
        raise ValueError(f'value of `-n/--index` must be greater than or equal to 1.')
    element = elements[namespace.index - 1]
    out = '\n'.join(str(ch).strip() for ch in element.children)
    if not namespace.no_copy:
        pyperclip.copy(out)
    if namespace.verbose:
        print(out)


if __name__ == '__main__':
    main()



