#! /usr/bin/env python3

import argparse
import os
import re
import json
import itertools
import shutil

from ipynb_common import path_iter, markdown_to_ipynb

MAX_HEADING_LEVEL = 2

TOC_NAME = 'index'
TITLE = '目次'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', required=True, help='Specify a path to a source directory.')
    parser.add_argument('-n', '--name', default=TOC_NAME, help='Specify the name of a TOC file (default: {TOC_NAME}).')
    parser.add_argument('-t', '--title', default=TITLE, help='Specify the title of TOC (default: {TITLE}).')    
    parser.add_argument('-l', '--max_heading_level', default=MAX_HEADING_LEVEL, help=f'Specify the max level of headings in TOC (default: {MAX_HEADING_LEVEL}).')
    parser.add_argument('-p', '--preamble', help='Specify the file of the preamble of TOC.')
    commandline_args = parser.parse_args()

    preamble = ''
    if commandline_args.preamble is not None:
        with open(commandline_args.preamble, encoding='utf-8') as f:
            preamble = f.read()

    ipynb = toc_ipynb(commandline_args.source, commandline_args.max_heading_level, commandline_args.title, preamble)
    with open(f'{commandline_args.name}.ipynb', 'w', encoding='utf-8') as f:
        json.dump(ipynb, f, indent=1, ensure_ascii=False)
        f.write('\n')
    rst = toc_rst(commandline_args.source, commandline_args.max_heading_level, commandline_args.title, preamble)
    with open(f'{commandline_args.name}.rst', 'w', encoding='utf-8') as f:
        f.write(rst)


def toc_rst(source, heading_depth, title, preamble):
    doclist = '\n   '.join(os.path.splitext(os.path.relpath(x, source))[0] for x in sorted(path_iter(source)))
    underline = '=' * (len(title) * 2)
    return f"""
{title}
{underline}
{preamble}

.. toctree::
   :maxdepth: {heading_depth}
   :glob:

   {doclist}
"""


def toc_ipynb(source, heading_level, title, preamble):
    markdown_lines = [f'# {title}\n', *preamble.splitlines(keepends=True), '\n']
    for notebook in sorted(path_iter(source)):
        with open(os.path.join(notebook), encoding='utf-8') as f:
            headings = extract_headings(json.load(f))
        level, heading = next(headings)
        assert level == 1, (level, heading)
        markdown_lines.append(f'## [{heading}]({os.path.relpath(notebook, source)})\n')
        markdown_lines.append('\n')
        markdown_lines.extend(('  ' * (lv - 2)) + f'- {h}\n' for lv, h in headings if lv <= heading_level)
        markdown_lines.append('\n')
    return markdown_to_ipynb(markdown_lines)


def extract_headings(ipynb):
    cells = ipynb['cells']
    source = itertools.chain.from_iterable(cell['source'] for cell in cells if cell['cell_type'] == 'markdown')

    toplevel = None
    is_inside_code_block = False
    for line in source:
        # コードブロックをスキップ
        triple_backquote_count = line.count('```')
        if triple_backquote_count > 0:
            assert triple_backquote_count == 1, ('A code block is incorrectly escaped.', line)
            is_inside_code_block = not is_inside_code_block
        if is_inside_code_block:
            continue

        # 見出しを解釈
        match_heading = re.match(r'\#+', line)
        if match_heading is not None:
            heading = line.lstrip('#').strip()
            if len(match_heading[0]) == 1 and toplevel is None:
                toplevel = heading
            else:
                assert len(match_heading[0]) != 1, 'Multiple top-level headings are found.'
            yield (len(match_heading[0]), heading)


if __name__ == '__main__':
    main()
