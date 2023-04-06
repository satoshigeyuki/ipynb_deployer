#! /usr/bin/env python3

import os
import re
import sys
import json
import itertools
import contextlib

import markdown

from ipynb_common import path_iter


def main():
    for base in sys.argv[1:]:
        for path in path_iter(base):
            with open(path, encoding='utf-8') as f:
                ipynb = json.load(f)
            nb = os.path.basename(path)
            check_html_tag(extract_markdowns(ipynb), nb)
            check_lists(extract_markdowns(ipynb), nb)
            check_spacing_around_code(extract_markdowns(ipynb), nb)


def check_lists(md_text, notebook):
    """
    Print warnings of lists in a style problematic for nbsphinx.
    False positives are due to line-wise checking.
    """
    md2html = markdown.Markdown().convert
    is_next_of_blank = True
    is_next_of_item = False
    for line in md_text:
        if line.strip() == '':
            is_next_of_blank = True
            is_next_of_item =  False
        else:
            htmlline = md2html(line)
            match_heading = re.match(r'(<ul>\s*?<li>.*?</li>\s*?</ul>)|(<ol>\s*?<li>.*?</li>\s*?</ol>)', htmlline)
            if match_heading is not None and not is_next_of_blank and not is_next_of_item:
                print('[ILL-STYLED] No blank before lists in Markdown.', notebook, line, sep=' | ', end='')
            is_next_of_blank = False
            is_next_of_item = match_heading is not None or is_next_of_item


def check_html_tag(md_text, notebook):
    for line in md_text:
        m = re.search('(<[a-zA-Z]+>)', line)
        if m is not None and m[1] != '<strong>':
            print(f'[ILL-STYLED] {m[1]} exists.', notebook, line, sep=' | ', end='')


def check_spacing_around_code(md_text, notebook):
    """
    Print warnings of spacing around code.
    It is according to general rules in Japanese text (i.e., Kinsoku Shori).
    """
    for line in md_text:
        m = re.search(r'```', line)
        if m is not None:
            if not line.startswith('```'):
                print('[ILL-STYLED] ``` appears not at BOL.', notebook, line, sep=' | ', end='')
            continue

        starter = [' ', '　', '。', '、', '）', ')', '（', '(', '・',  '：', '「', '#', '[']
        closer = [' ', '\n', '。', '、', '（', '）', ')', ',', '・', '」', ']']
        terms = set()
        with contextlib.suppress(StopIteration):
            for code_pat in (r'\*\*`(.*?)`\*\*', r'<strong>`(.*?)`</strong>', r'`(.*?)`'):
                for m in re.finditer(code_pat, line):
                    if m[1] in terms:
                        continue
                    terms.add(m[1])
                    if not any(line.startswith(m[0] + suf) for suf in closer) and \
                       not any(pre + m[0] + suf in line for pre in starter for suf in closer):
                        print('[ILL-STYLED] Spacing around code is inappropriate.', notebook, line, sep=' | ', end='')
                        raise StopIteration


def extract_markdowns(ipynb):
    cells = ipynb['cells']
    source = itertools.chain.from_iterable(cell['source'] for cell in cells if cell['cell_type'] == 'markdown')
    is_inside_code_block = False
    for line in source:
        # Skip code block
        triple_backquote_count = line.count('```')
        if triple_backquote_count > 0:
            assert triple_backquote_count == 1, ('A code block is incorrectly escaped.', notebook, line)
            is_inside_code_block = not is_inside_code_block
            continue
        if is_inside_code_block:
            continue
        yield line if line.endswith('\n') else line + '\n'


if __name__ == '__main__':
    main()
