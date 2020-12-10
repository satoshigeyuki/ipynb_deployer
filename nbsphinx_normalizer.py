#! /usr/bin/env python3

import os
import re
import sys
import json
import argparse

import markdown


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', nargs='*', required=True, default=[], help='Specify source ipynb file(s).')
    parser.add_argument('-d', '--dest_dir', default='.', help=f'Specify a directory to place output (default: the current directory).')
    commandline_args = parser.parse_args()
    
    assert os.path.isdir(commandline_args.dest_dir)
    for source in commandline_args.source:
        assert commandline_args.source.endswith('.ipynb')
        sanitize_ipynb(source, os.path.join(commandline_args.dest_dir, source))


def sanitize_ipynb(source, dest):
    with open(source, encoding='utf-8') as f:
        ipynb = json.load(f)
    ipynb['cells'] = [sanitize_cell(x) for x in ipynb['cells']]
    with open(dest, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(ipynb, f, indent=1, ensure_ascii=False)
        f.write('\n')


def sanitize_cell(cell):
    if cell['cell_type'] == 'markdown':
        cell['source'] = sanitize_markdown(''.join(cell['source']))
    return cell


def sanitize_markdown(md):
    md2html = markdown.Markdown().convert
    is_inside_code_block = False
    source_cell = []
    for line in md.splitlines(keepends=True):
        # Skip code block
        triple_backquote_count = line.count('```')
        if triple_backquote_count > 0:
            assert triple_backquote_count == 1, ('A code block is incorrectly escaped.', line)
            assert re.match('^```.*$', line) is not None, ('A triple backquote appears (```) inappropriately.', line)
            line = '```\n' # Remove language declaration from code block
            is_inside_code_block = not is_inside_code_block
        if is_inside_code_block:
            source_cell.append(line)
            continue

        sanitized_line = line

        # Remove horizontal rule
        if re.match('^\s*---\s*', sanitized_line) is not None:
            sanitized_line = '\n'

        # Unique alt text of img: Cf. https://github.com/spatialaudio/nbsphinx/issues/162
        for m in re.finditer(r'!\[.*?\]\((.*?)\)', sanitized_line):
            alt_text = m[1].replace('-', '--').replace('_', '-')
            sanitized_line = sanitized_line.replace(m[0], f'![{alt_text}]({m[1]})')

        # Remove strong attached to code
        for code in re.findall(r'<strong><code>(.*?)</code></strong>', md2html(sanitized_line)):
            code = code.replace('&lt;', '<').replace('&gt;', '>')
            sanitized_line = sanitized_line.replace(f'**`{code}`**', f'`{code}`').replace(f'<strong>`{code}`</strong>', f'`{code}`')

        # Remove code, string, and \ from anchor text
        for m in re.finditer(r'<a href="(.*?)">(.*?)</a>', md2html(sanitized_line)):
            markdown_text = re.sub(r'</?code>', '`', m[2])
            sanitized_text = re.sub(r'</?code>', '', m[2])
            markdown_text = re.sub(r'</?strong>', '**', markdown_text)
            sanitized_text = re.sub(r'</?strong>', '', sanitized_text)
            sanitized_text = sanitized_text.replace('\\', '')
            sanitized_line = sanitized_line.replace(f'[{markdown_text}]({m[1]})', f'[{sanitized_text}]({m[1]})')

        source_cell.append(sanitized_line)
    return source_cell


if __name__ == '__main__':
    main()
