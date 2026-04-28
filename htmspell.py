import argparse
import configuration
import os
import sys
from pathlib import Path
from spelling import SpellChecker


def make_argument_parser():
    parser = argparse.ArgumentParser(description="A tool for spell-checking HTML files with custom dictionaries.")
    subparsers = parser.add_subparsers(dest='command')
    config_parser = subparsers.add_parser('config')
    config_parser.add_argument('--new', action="store_true")
    config_parser.add_argument('-f', '--file', nargs=1, action="store", type=Path,
                               help="Specify a file path for --make-config.")

    check_parser = subparsers.add_parser('check')
    check_parser.add_argument('filenames', nargs='+', type=Path)
    provisions = check_parser.add_argument_group(title="Provisions",
                                                 description="Information supplied to enable spell checking.")
    provisions.add_argument('-c', '--config', nargs=1, action="store", type=Path)
    provisions.add_argument('-e', '--elements', type=str,
                            help="A comma-separated list of HTML element types to check.")
    using_group = provisions.add_mutually_exclusive_group()
    using_group.add_argument('-u', '--using', action='store',
                             help="Select additional dictionaries by name, separated by columns."
                             " When not selected, interactive mode is used.")
    using_group.add_argument('-a', '--all', '--using-all', action='store_true',
                             help='Use all dictionaries specified by config file.')
    provisions.add_argument('-d', '--dehyphenate', action='store_true',
                            help="Spell check hyphenated words by their component parts.")
    provisions.add_argument('-k', '--ignore-enclitics', action='store_true',
                            help="Remove certain enclitics and spell check base lemmas.")
    provisions.add_argument('-s', '--enclitics', action="store",
                            help="Override config file enclitics with comma-separated strings.")
    return parser


def main():
    parser = make_argument_parser()
    namespace = parser.parse_args()
    match namespace.command:
        case 'config':
            configure(namespace)
        case 'check':
            check(namespace)


def configure(namespace: argparse.Namespace):
    if namespace.new:
        new_config_file = configuration.make_default(namespace.file or Path(os.getcwd()))
        print(f"New configuration file created: {new_config_file!s}")
        print("If this file will be your preferred HTMSpell configuration, you should", end=" ")
        print("set the environment variable `HTMSPELL_CONFIG` to its path.")
    else:
        current_config_file = configuration.find_current()
        print(f"Current HTMSpell configuration: {current_config_file!s}")
        if current_config_file is None:
            print("No HTMSpell configuration detected.")
            print(f"Create a new configuration file with `{sys.argv[0]} config --new`",
                  f"or assign an existing configuration's file path to {configuration.ENV_KEY}.")

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


def dictionary_menu(dictionaries: list[dict]) -> list[Path]:
    menu = {d['name']: d['path'] for d in dictionaries}
    index_map = dict(enumerate(sorted(menu.keys()), start=1))
    selected = None
    while selected is None:
        print("Configured dictionaries:")
        largest_index = max(index_map.keys())
        padded_size = len(str(largest_index))
        for index, name in index_map.items():
            item_number = str(index).rjust(padded_size, ' ')
            print(f'  {item_number}) {name}')
        captured = input('Enter the numbers for additional dictionaries to use, separating multiple\n'
                         'selections with commas (or leave blank for none): ')
        if not captured.strip():
            selected = []
        else:
            try:
                item_numbers = set(parse_selection(captured))
                valid_selection(item_numbers, set(index_map.keys()))
            except (TypeError, ValueError) as e:
                print(f"{e!s}. Try again.\n")
                continue
            selected = list(item_numbers)
        print()
    selected_names = [index_map[x] for x in selected]
    print("Dictionaries selected:", ", ".join(sorted(selected_names)))
    return [menu[name] for name in selected_names]



def main_dictionary_path(config: dict) -> Path:
    if (first := Path(config['main-dictionary']['path'])).exists():
        return first
    if (fallback := Path(config['main-dictionary']['fallback'])).exists():
        return fallback
    raise FileNotFoundError("Neither `path` nor `fallback` contains a valid path to a dictionary."
                            " Check your configuration file.")


def check(namespace: argparse.Namespace):
    config = configuration.load_config(namespace.config)
    if namespace.elements:
        elements = namespace.elements.split(',')
    else:
        elements = config['search']['html_elements']
    dictionaries = [main_dictionary_path(config)]
    if namespace.all:
        dictionaries.extend(d['path'] for d in config['dictionaries'])
    elif namespace.using is None:
        dictionaries.extend(dictionary_menu(config['dictionaries']) if 'dictionaries' in config else [])
    else:
        for name in namespace.using.split(','):
            for dictionary in config['dictionaries']:
                if dictionary['name'] == name:
                    dictionaries.append(dictionary['path'])
                    break
            else:
                raise ValueError(f'no dictionary named {name} in config file.')

    enclitics = namespace.enclitics or config.get('cleaning', {}).get('enclitics', [])

    sc = SpellChecker(set(dictionaries), elements)
    here = Path(os.getcwd())
    for filename in namespace.filenames:
        print(absolute := here / filename)
        try:
            typos = sc.check_spelling(absolute,
                                      enclitics=enclitics,
                                      dehyphenate=namespace.dehyphenate,
                                      ignore_enclitics=namespace.ignore_enclitics)
        except FileNotFoundError as e:
            print(f"  {e!s}")
        else:
            for t in typos:
                print(f'  {t!s}')

if __name__ == '__main__':
    main()
