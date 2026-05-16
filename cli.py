import argparse
import re
from pathlib import Path


def location(s: str) -> tuple[str, int]:
    try:
        element, index = s.split('.')
    except ValueError:
        raise ValueError('`--location` argument must take the form `element.index` (e.g. `p.7`)')
    return element, int(index)


def indices(s: str) -> list[int]:
    return [int(x) for x in s.split(',')]


def make_argument_parser():
    parser = argparse.ArgumentParser(description="A tool for spell checking HTML files with custom dictionaries.")
    subparsers = parser.add_subparsers(dest='command')

    # Configuration subparser
    config_parser = subparsers.add_parser('config')
    config_parser.add_argument('-n', '--new', action="store_true")
    config_parser.add_argument('-f', '--file', nargs=1, action="store", type=Path,
                               help="Specify a file path for `--new`.")

    # Spell checking subparser
    check_parser = subparsers.add_parser('check')
    check_parser.add_argument('filenames', nargs='+', type=Path)
    provisions = check_parser.add_argument_group(title="Provisions",
                                                 description="Information supplied to enable spell checking, "
                                                             "including overrides to the config file.")
    provisions.add_argument('-c', '--config', nargs=1, action="store", type=Path)
    using_group = provisions.add_mutually_exclusive_group()
    provisions.add_argument('-d', '--dehyphenate', action='store_true',
                            help="Spell check hyphenated words by their component parts.")
    provisions.add_argument('-k', '--ignore-enclitics', action='store_true',
                            help="Remove certain enclitics and spell check base lemmas.")
    provisions.add_argument('-s', '--enclitics', action="store",
                            help="Override config file enclitics with comma-separated strings.")
    provisions.add_argument('-i', '--ignore-capitalized', action="store_true",
                            help="Skip proper nouns and other capitalized words.")
    provisions.add_argument('-e', '--elements', type=str,
                            help="A comma-separated list of HTML element types to check.")
    provisions.add_argument('-p', '--problems', '--problem', action='store', type=str,
                            help=("Comma-separated list of choices of which matching conditions should be considered "
                                 "spelling errors. Choices: NotFound, Casefolded, Capitalized, AllCaps. "
                                 "Default configuration: NotFound,Capitalized,AllCaps"),
                            default="NotFound,Capitalized,AllCaps")
    using_group.add_argument('-u', '--using', action='store',
                             help="Select additional dictionaries by name, separated by columns."
                             " When not selected, interactive mode is used.")
    using_group.add_argument('-a', '--all', '--using-all', action='store_true',
                             help='Use all dictionaries specified by config file.')

    # Word count subparser
    count_parser = subparsers.add_parser('count')
    count_parser.add_argument('filenames', nargs='+', type=Path)
    count_parser.add_argument('-d', '--dehyphenate', action='store_true',
                              help="Count hyphenated words by their component parts.")
    count_parser.add_argument('-e', '--elements', type=str,
                              help="A comma-separated list of HTML element types to check")
    count_parser.add_argument('-r', '--regex', action='store', type=re.compile,
                              help="A specific term to count instances of within the selected file(s).")
    count_parser.add_argument('-q', '--quiet', action='store_true',
                              help="Suppress intermediate outputs and only show the overall results.")

    # Element lookup subparser
    show_parser = subparsers.add_parser('show')
    show_parser.add_argument('filename', type=Path)
    show_parser.add_argument('-e', '--element', type=str,
                             help="A single type of HTML element.")
    show_parser.add_argument('-i', '--index', '--indices', type=indices,
                           help="Comma-separated series of element numbers to display.")
    show_parser.add_argument('-l', '--location', '--loc', type=location,
                                help="Compact form for locating a single element, using the same syntax"
                                     + " as the output of `check` and `count` commands, e.g. `p.7` or"
                                     + " td.12")
    return parser
