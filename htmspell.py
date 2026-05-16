import argparse
from collections import Counter

import configuration
import os
import sys
from pathlib import Path

import cli
from configuration import main_dictionary_path
from spelling import SpellChecker, EntryMatch
from document import DOM
from utils import parse_selection, valid_selection


def qprint(*args, **kwargs):
    if kwargs.pop('quiet', False):
        return None
    return print(*args, **kwargs)


def main():
    parser = cli.make_argument_parser()
    namespace = parser.parse_args()
    match namespace.command:
        case 'config':
            configure(namespace)
        case 'check':
            check(namespace)
        case 'count':
            count(namespace)
        case 'show':
            show(namespace)
        case _:
            raise Exception('unhandled subcommand: ', namespace.command)


def configure(namespace: argparse.Namespace):
    if namespace.new:
        new_config_file = configuration.make_default(namespace.file or Path(os.getcwd()))
        print(f"New configuration file created: {new_config_file!s}")
        print("If this file will be your preferred HTMSpell configuration, you should "
              "set the environment variable `HTMSPELL_CONFIG` to its path.")
    else:
        current_config_file = configuration.find_current()
        print(f"Current HTMSpell configuration: {current_config_file!s}")
        if current_config_file is None:
            print("No HTMSpell configuration detected.")
            print(f"Create a new configuration file with `{sys.argv[0]} config --new`",
                  f"or assign an existing configuration's file path to {configuration.ENV_KEY}.")


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
    problems = EntryMatch.parse_problems(namespace.problems)
    sc = SpellChecker(set(dictionaries), elements, problems=problems)
    for filename in namespace.filenames:
        print(filename)
        try:
            typos = sc.check_spelling(filename,
                                      enclitics=enclitics,
                                      dehyphenate=namespace.dehyphenate,
                                      ignore_enclitics=namespace.ignore_enclitics,
                                      ignore_capitalized=namespace.ignore_capitalized)
        except FileNotFoundError as e:
            print(f"  {e!s}")
        else:
            for t in typos:
                print(f'  {t!s}')

def count(namespace: argparse.Namespace):
    total_words = 0
    total_elements = Counter()
    total_unpaired = 0
    total_searched = 0 if namespace.regex else None
    quiet = namespace.quiet and len(namespace.filenames) > 1
    for filename in namespace.filenames:
        qprint(filename, quiet=quiet)
        d = DOM(filename)
        word_count = d.count_words(dehyphenate=namespace.dehyphenate)
        element_counts = d.count_elements(elements=namespace.elements)
        unpaired_characters = d.unpaired_characters(elements=namespace.elements)
        regex_searched = d.count_instance_of(namespace.regex) if total_searched is not None else None
        qprint(f'  words: {word_count}', quiet=quiet)
        qprint('  elements of interest:', quiet=quiet)
        for element_type, c in element_counts.most_common():
            qprint(f'    {element_type}: {c}', quiet=quiet)
        if unpaired_characters:
            total_unpaired += len(unpaired_characters)
            qprint('  unpaired characters:', quiet=quiet)
            for etype, eindex, char in unpaired_characters:
                qprint(f'    {etype}.{eindex}: {char}', quiet=quiet)
        if regex_searched is not None:
            total_searched += regex_searched
            qprint(f'  {namespace.regex.pattern!r} count: {regex_searched}', quiet=quiet)
        total_words += word_count
        total_elements += element_counts
        qprint(quiet=quiet)

    if len(namespace.filenames) > 1:
        print('Overall:')
        print(f'  words: {total_words}')
        print('  elements of interest:')
        for element_type, c in total_elements.most_common():
            print(f'    {element_type}: {c}')
        if total_words is not None:
            print(f'  {namespace.regex.pattern!r} count: {total_searched}')
    return


def show(namespace: argparse.Namespace):
    d = DOM(namespace.filename)
    if namespace.location:
        el, ind = namespace.location
        print(d.get(el, ind))
    else:
        for index in namespace.index:
            print(d.get(namespace.element, index), end="\n\n")



if __name__ == '__main__':
    main()
