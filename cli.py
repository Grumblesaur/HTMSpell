import argparse
import re
import locale
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
    config_parser = subparsers.add_parser('config', help='Create a configuration file for this program')
    config_parser.add_argument('-n', '--new', action="store_true",
                               help="Create a new configuration file")
    config_parser.add_argument('-f', '--file', nargs=1, action="store", type=Path,
                               help="Specify a file path for `--new`.")

    # Spell checking subparser
    check_parser = subparsers.add_parser('check', help='Check spelling')
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
    using_group.add_argument('-n', '--none', '--using-none', action="store_true",
                             help='Use no dictionaries but the main one.')

    # Word count subparser
    count_parser = subparsers.add_parser('count',
                                         help='Count words overall or specific instances of a particular word or regex')
    count_parser.add_argument('filenames', nargs='+', type=Path)
    count_parser.add_argument('-d', '--dehyphenate', action='store_true',
                              help="Count hyphenated words by their component parts.")
    count_parser.add_argument('-e', '--elements', type=str,
                              help="A comma-separated list of HTML element types to check")
    count_parser.add_argument('-r', '--regex', action='store', type=re.compile,
                              help="A specific term to count instances of within the selected file(s).")
    count_parser.add_argument('-q', '--quiet', action='store_true',
                              help="Suppress intermediate outputs and only show the overall results.")

    # Corpus linguistics subparser
    corpus_parser = subparsers.add_parser('corpus', help="Check word counts for corpus linguistics purposes")
    corpus_parser.add_argument('filenames', nargs='+', type=Path)
    corpus_parser.add_argument('-c', '--config', nargs=1, action="store", type=Path)
    corpus_parser.add_argument('-d', '--dehyphenate', action='store_true',
                               help="Count hyphenated words as their component parts")
    corpus_parser.add_argument('-s', '--enclitics', action="store",
                            help="Override config file enclitics with comma-separated strings.")
    corpus_enclitics = corpus_parser.add_mutually_exclusive_group(required=False)
    corpus_enclitics.add_argument('-k', '--ignore-enclitics', action='store_true',
                               help="Count lemmas with enclitics stripped off.")
    corpus_enclitics.add_argument('-p', '--split-enclitics', action='store_true',
                               help="Count enclitics as separate lemmas.")
    corpus_parser.add_argument('-z', '--drop-stopwords', action="store_true",
                               help="Ignore common words such as 'the', 'and', 'in', etc.")
    corpus_parser.add_argument('-t', '--language', type=str,
                               default=locale.getlocale()[0].split('_')[0],
                               help="ISO-639-1 language code (or full name) of desired language for stopwords")
    corpus_thresholds = corpus_parser.add_mutually_exclusive_group()
    corpus_thresholds.add_argument('-g', '--count-greater-than', type=int,
                                   help='Show all words used more than `M` times')
    corpus_thresholds.add_argument('-G', '--count-greater-equal', type=int,
                                   help='Show all words used at least `M` times')
    corpus_thresholds.add_argument('-l', '--count-less-than', type=int,
                                   help="Show all words used less than `M` times")
    corpus_thresholds.add_argument('-L', '--count-less-equal', type=int,
                                   help="Show all words used no more than `M` times")

    # Element lookup subparser
    show_parser = subparsers.add_parser('show', help="Display a portion of the DOM by element type and index")
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
