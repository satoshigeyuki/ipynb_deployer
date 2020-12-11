#! /usr/bin/env python3

import os
import sys
import json
import argparse

from toc_generator import path_iter

if (sys.version_info.major, sys.version_info.minor) < (3, 8):
    print('[ERROR] This script requires Python >= 3.8.')
    sys.exit(1)

COMMON_METADATA = {
    'kernelspec': {
        'display_name': 'Python 3',
        'language': 'python',
        'name': 'python3',
    },
    'language_info': {
        'name': '',
    },
}

PRESERVED_METADATA_KEYS = ('tags', 'nbsphinx')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', nargs='*', required=True, default=[], help='Specify source(s) of ipynb file or directory.')
    parser.add_argument('-i', '--interactive', action='store_true', help=f'Remove metadata interactively.')
    parser.add_argument('-p', '--preserved_keys', nargs='*', default=[], metavar='METADATA_KEY', help=f'Specify preserved key(s) of metadata.')
    commandline_args = parser.parse_args()

    preserved = set(PRESERVED_METADATA_KEYS)
    preserved.update(commandline_args.preserved_keys)
    for base in commandline_args.source:
        for path in path_iter(base):
            cleanup_ipynb(path, path, preserved, commandline_args.interactive)


def cleanup_ipynb(source, dest, preserved, interactive):
    with open(source, encoding='utf-8') as f:
        ipynb = json.load(f)
    cleanup_metadata(ipynb['metadata'], os.path.basename(source), preserved, interactive)
    cleanup_cells(ipynb['cells'], os.path.basename(source), preserved, interactive)
    with open(dest, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(ipynb, f, indent=1, ensure_ascii=False)
        f.write('\n')


def cleanup_metadata(metadata, notebook, preserved, interactive):
    metadata_new = COMMON_METADATA.copy()
    for k, v in metadata.items():
        if k in COMMON_METADATA:
            if v != COMMON_METADATA[k]:
                print(f'[INFO] Reset the entry `{repr(k)}: {repr(v)}` at {notebook}.')
        elif k in preserved:
            print(f"[INFO] Metadata item `{repr(k)}: {repr(v)}` at {notebook}.")
            metadata_new[k] = v
        elif interactive:
            print(f"[WARNING] The metadata of `{notebook}` have the item `{repr(k)}: {repr(v)}`.")
            if not yesno_question('Remove this item?'):
               metadata_new[k] = v
        else:
            print(f"[INFO] Remove the item `{repr(k)}: {repr(v)}` of the metadata of `{notebook}`.")
    metadata.clear()
    metadata.update(metadata_new)


def cleanup_cells(cells, notebook, preserved, interactive):
    for c in cells:
        if c['cell_type'] == 'code':
            c['execution_count'] = None
            c['outputs'] = []
        metadata = {}
        for k, v in c['metadata'].items():
            if k in preserved:
                print(f"[INFO] Metadata item `{repr(k)}: {repr(v)}` at the cell `{repr(''.join(c['source']))}` in `{notebook}`.")
                metadata[k] = v
            elif interactive:
                print(f"[WARNING] The metadata of a cell of `{notebook}` have the item `{repr(k)}: {repr(v)}`.")
                if not yesno_question('Remove this item?'):
                    metadata[k] = v
            else:
                print(f"[INFO] Remove the item `{repr(k)}: {repr(v)}` of the metadata of a cell of `{notebook}`.")
        c['metadata'] = metadata


def yesno_question(message):
    while True:
        while answer := input(f'{message} [y/n]: '):
            if (first_alphabet := answer[0].lower()) in 'yn':
                return (first_alphabet == 'y')
            print(f'Error. `{answer}` is not a valid answer to this question.')


if __name__ == '__main__':
    main()
