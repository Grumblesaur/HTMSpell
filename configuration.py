import tomllib
import os
from pathlib import Path

TOML_DEFAULT_NAME = "htmslspell.toml"
ENV_KEY = "HTMSPELL_CONFIG"
TOML_DEFAULT = """
title = "HTMSpell Configuration"

[search]
html_elements = ["p", "td", "th"]

[cleaning]
enclitics = ["'ll", "'re", "'d", "'s", "'ve"]

[main-dictionary]
path = "/usr/share/dict/words"
fallback = "/usr/dict/words"

# You can add new dictionaries to your configuration. Create a new section
# headed by `[[dictionaries]]`, and place under it a `name` field and a
# `path` field, e.g.:
#
# [[dictionaries]]
# name = "Magic Words"
# path = "/home/your-name/wordlists/arcana.txt"
#
# When running HTMSpell interactively, such entries will be offered as
# choices for your word sources. This allows you to track domain-specific
# vocabulary (e.g. fictional worlds, hobby jargon, words borrowed from
# other languages) without polluting your system's main dictionary.
# For non-interactive use of HTMSpell, you can pass the names of the
# dictionaries you wish to use, separated by commas, to the
# `--using` argument.
#
"""


def make_default(directory: Path) -> Path:
    if (destination := directory / TOML_DEFAULT_NAME).exists():
        raise FileExistsError(f'{destination!s} already exists. Remove it, rename it, or specify a path with `--file`.')
    with open(saved_to := directory / TOML_DEFAULT_NAME, 'w', encoding='utf-8') as f:
        f.write(TOML_DEFAULT)
    return saved_to


def find_current() -> Path | None:
    local = Path(os.getcwd()) / 'htmspell.toml'
    if local.exists():
        return local
    if (env_defined := Path(os.environ.get(ENV_KEY))).exists():
        return env_defined
    return None


def load_config(from_path: Path = None) -> dict:
    if from_path is None:
        cwd = Path(os.getcwd())
        default_toml_path = cwd / TOML_DEFAULT_NAME
        if not default_toml_path.exists():
            load_path = Path(os.environ[ENV_KEY])
        else:
            load_path = default_toml_path
    else:
        load_path = from_path

    with open(load_path, 'rb') as f:
        return tomllib.load(f)
