#! /usr/bin/env python3

import os
import re
import json
import argparse
import itertools
import collections
import html

import markdown

from ipynb_common import path_iter, markdown_to_ipynb

INDEX_NAME = 'index_of_terms'
TITLE = '索引'

MAX_HEADING_LEVEL = 3


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', required=True, help='Specify a source directory.')
    parser.add_argument('-d', '--dest_dir', required=True, help='Specify a directory to place an index.')
    parser.add_argument('-n', '--name', default=INDEX_NAME, help=f'Specify the name of an index file (default: {INDEX_NAME}).')
    parser.add_argument('-y', '--yomi_dict', help='Specify a yomigana dictionary of indexed tems.')
    commandline_args = parser.parse_args()

    assert os.path.isdir(commandline_args.source)
    assert os.path.isdir(commandline_args.dest_dir)

    yomi_dict = {}
    if commandline_args.yomi_dict:
        with open(commandline_args.yomi_dict, encoding='utf_8') as f:
            yomi_dict = json.load(f)
    term_normalizer = make_lexicographical_normalizer(yomi_dict)

    index = index_terms(path_iter(commandline_args.source))
    ipynb = markdown_to_ipynb(convert_to_markdown_lines(index, commandline_args.dest_dir, sorting_key=term_normalizer))
    with open(os.path.join(commandline_args.dest_dir, f'{commandline_args.name}.ipynb'), 'w', encoding='utf-8') as f:
        json.dump(ipynb, f, indent=1, ensure_ascii=False)
        f.write('\n')


def index_terms(notebooks, *, heading_level=MAX_HEADING_LEVEL):
    md2html = markdown.Markdown().convert
    term_index = collections.defaultdict(list)

    for notebook in notebooks:
        with open(notebook, encoding='utf_8') as f:
            cells = json.load(f)['cells']
        source = itertools.chain.from_iterable(cell['source'] for cell in cells if cell['cell_type'] == 'markdown')

        headings = set()
        current_heading = None
        is_inside_code_block = False
        for line in source:
            # Skip code block
            triple_backquote_count = line.count('```')
            if triple_backquote_count > 0:
                assert triple_backquote_count == 1, ('A code block is incorrectly escaped.', notebook, line)
                is_inside_code_block = not is_inside_code_block
            if is_inside_code_block:
                continue

            # Update the heading of the current section
            match_heading = re.match(r'\#+', line)
            if match_heading is not None and len(match_heading[0]) <= heading_level:
                current_heading = line.lstrip('#').strip()
                if current_heading in headings:
                    print(f'[WARNING] Heading `{current_heading}` collided in `{notebook}`.')
                else:
                    headings.add(current_heading)

            # Collect indexed terms
            for term in re.findall(r'<strong>(.*?)</strong>', md2html(line)):
                # Exclude <strong><em>...</em></strong> (i.e., something enclosed by ***)
                if term.startswith('<em>'):
                    continue

                term = re.sub(r'</?code>', '`', term)
                # Remove function call parentheses
                if term.endswith('()`'):
                    term = term[:-len('()`')] + '`'

                term_index[term].append((notebook, current_heading))

    return term_index


def make_lexicographical_normalizer(yomi_dict):
    hiragana = 'あいうえお' \
               'かきくけこ' \
               'さしすせそ' \
               'たちつてと' \
               'なにぬねの' \
               'はひふへほ' \
               'まみむめも' \
               'やゆよ'     \
               'らりるれろ' \
               'わおん'     \
               'がぎぐげご' \
               'ざじずぜぞ' \
               'だぢづでど' \
               'ばびぶべぼ' \
               'ぱぴぷぺぽ'

    katakana = 'アイウエオ' \
               'カキクケコ' \
               'サシスセソ' \
               'タチツテト' \
               'ナニヌネノ' \
               'ハヒフヘホ' \
               'マミムメモ' \
               'ヤユヨ'     \
               'ラリルレロ' \
               'ワオン'     \
               'ガギグゲゴ' \
               'ザジズゼゾ' \
               'ダヂヅデド' \
               'バビブベボ' \
               'パピプペポ'

    hira_to_kata = dict(zip(hiragana, katakana))

    def normalize(s):
        s = s.replace('`', '')
        return ''.join(hira_to_kata.get(c, c) for c in yomi_dict.get(s, s))

    return normalize


def convert_to_markdown_lines(index_terms, base_dir, *, title=TITLE, sorting_key=None):
    md2html = markdown.Markdown().convert
    lines = [f'# {title}\n', '\n']
    for term in sorted(index_terms, key=sorting_key):
        refs = []
        for notebook, heading in index_terms[term]:
            notebook = os.path.relpath(notebook, base_dir)
            # Remove strong from heading
            for ref in re.findall(r'<strong>(.*?)</strong>',  md2html(heading)):
                ref = re.sub(r'</?code>', '`', ref)
                heading = heading.replace(f'**{ref}**', ref).replace(f'<strong>{ref}</strong>', ref)
            # Create links
            link = heading
            for code in re.findall(r'<code>(.*?)</code>', md2html(link)):
                link = link.replace(f'`{code}`', code)
            link = re.sub(r'\s+', '-', link.strip())
            refs.append(f'[{os.path.splitext(notebook)[0]}#{heading}]({notebook}#{link})')
        lines.append(f'- {html.unescape(term)} {", ".join(refs)}\n')
    return lines


if __name__ == '__main__':
    main()
