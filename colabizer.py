#! /usr/bin/env python3

import argparse
import os
import re
import sys
import json
import shutil
import io
import contextlib

if (sys.version_info.major, sys.version_info.minor) < (3, 8):
    print('[ERROR] This script requires Python >= 3.8.')
    sys.exit(1)

PUBLIC_DIR = 'docs'
DEST_DIR = 'colab'
URL_BASE = 'https://username.github.io/reponame/'

IGNORE_PATTERNS = ('.*', '*~', '__pycache__')

DOWNLOAD_IGNORE_FILE = '.download_ignore'

HEADER_NOTICE = """
##================================================
## このセルを最初に実行せよ---Run this cell first.
##================================================
""".lstrip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--public_dir', default=PUBLIC_DIR, help=f'Specify PUBLIC_DIR for external files (default: {PUBLIC_DIR}).')
    parser.add_argument('-d', '--dest_dir', default=DEST_DIR, help=f'Specify DEST_DIR for Colab ipynb  (default: {DEST_DIR}).')
    parser.add_argument('-b', '--url_base', default=URL_BASE, help=f'Specify URL_BASE for external files (default: {URL_BASE}).')
    parser.add_argument('-s', '--soruce', nargs='*', required=True, default=[], help='Specify source(s) of ipynb file or directory.')
    commandline_args = parser.parse_args()
    for source in commandline_args.soruce:
        if os.path.isdir(source):
            colabize_directory(source, commandline_args.public_dir, commandline_args.dest_dir, commandline_args.url_base)
        else:
            colabize_ipynb(source, commandline_args.public_dir, commandline_args.dest_dir, commandline_args.url_base)


def colabize_ipynb(source, public_base, dest_base, url_base, ignore_patterns=None):
    source_dir, filename = os.path.split(source)
    source_dir = os.path.relpath(source_dir)
    assert not source_dir.startswith('..')
    assert filename.endswith('.ipynb')
    public_dir = os.path.join(public_base, source_dir)
    ignore = shutil.ignore_patterns('*.ipynb', *(IGNORE_PATTERNS if ignore_patterns is None else ignore_patterns))
    shutil.copytree(source_dir, public_dir, ignore=ignore, dirs_exist_ok=True)

    try:
        with open(os.path.join(source_dir, DOWNLOAD_IGNORE_FILE), encoding='utf-8') as f:
            ignore = shutil.ignore_patterns(*f.read().splitlines())
    except FileNotFoundError:
        ignore = None

    with open(source, encoding='utf-8') as f:
        ipynb = json.load(f)
    ref_imgs = replace_img_links(ipynb['cells'], os.path.join(url_base, source_dir))
    header = make_colab_header(public_dir, public_base, url_base, ref_imgs, ignore)
    if header['source']:
        ipynb['cells'].insert(0, header)
    os.makedirs(os.path.join(dest_base, source_dir), exist_ok=True)
    with open(os.path.join(dest_base, source_dir, filename), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(ipynb, f, indent=1, ensure_ascii=False)
        f.write('\n')


def colabize_directory(source_dir, public_base, dest_base, url_base, ignore_patterns=None):
    source_dir = os.path.relpath(source_dir)
    assert not source_dir.startswith('..')
    public_dir = os.path.join(public_base, source_dir)
    ignore = shutil.ignore_patterns('*.ipynb', *(IGNORE_PATTERNS if ignore_patterns is None else ignore_patterns))
    shutil.copytree(source_dir, public_dir, ignore=ignore, dirs_exist_ok=True)

    ignore = shutil.ignore_patterns(*IGNORE_PATTERNS)
    for (dirpath, dirs, fnames) in os.walk(source_dir):
        ignored_dirs = set(ignore(dirpath, dirs))
        dirs[:] = filter(lambda x: x not in ignored_dirs, dirs)
        ipynb_files = (x for x in fnames if x.endswith('.ipynb'))
        dl_ignore_patterns = ['*.ipynb']
        with contextlib.suppress(FileNotFoundError):
            with open(os.path.join(dirpath, DOWNLOAD_IGNORE_FILE), encoding='utf-8') as f:
                dl_ignore_patterns.extend(f.read().splitlines())
        dl_ignore = shutil.ignore_patterns(*dl_ignore_patterns)
        for filename in ipynb_files:
            source_path = os.path.join(dirpath, filename)
            with open(source_path, encoding='utf-8') as f:
                ipynb = json.load(f)
            ref_imgs = replace_img_links(ipynb['cells'], os.path.join(url_base, source_dir))
            header = make_colab_header(os.path.join(public_dir, os.path.relpath(dirpath, source_dir)), public_base, url_base, ref_imgs, dl_ignore)
            if header['source']:
                ipynb['cells'].insert(0, header)
            os.makedirs(os.path.join(dest_base, dirpath), exist_ok=True)
            with open(os.path.join(dest_base, source_path), 'w', encoding='utf-8', newline='\n') as f:
                json.dump(ipynb, f, indent=1, ensure_ascii=False)
                f.write('\n')


def make_colab_header(target_dir, target_base, url_base, ref_imgs, ignore=None):
    code_lines = []
    for path, dirs, fnames in os.walk(target_dir):
        ignored_dirs = set(ignore(path, dirs) if ignore else [])
        ignored_files = set(ignore(path, fnames) if ignore else [])
        dirs[:] = filter(lambda x: x not in ignored_dirs, dirs)
        fnames[:] = filter(lambda x: x not in ignored_files, fnames)
        public_dir = os.path.relpath(path, target_base)
        reldir = os.path.relpath(path, target_dir)
        code_lines.extend(f'!wget -P {reldir} {os.path.join(url_base, public_dir, fname)}\n'
                          for fname in fnames if os.path.relpath(os.path.join(reldir, fname)) not in ref_imgs)
    if code_lines:
        code_lines[-1] = code_lines[-1].rstrip()
        code_lines = HEADER_NOTICE.splitlines(True) + code_lines
    return {'cell_type': 'code',
            'execution_count': None,
            'metadata': {},
            'outputs': [],
            'source': code_lines}


def replace_img_links(cells, base_url):
    ref_imgs = []
    for cell in cells:
        if cell['cell_type'] != 'markdown':
            continue
        is_inside_code_block = False
        source_cell = []
        for line in io.StringIO(''.join(cell['source'])):
            # コードブロックをスキップ
            triple_backquote_count = line.count('```')
            if triple_backquote_count > 0:
                assert triple_backquote_count == 1, ('A code block is incorrectly escaped.', line)
                is_inside_code_block = not is_inside_code_block
            if is_inside_code_block:
                source_cell.append(line)
                continue
            # 画像参照をWebリンクに置換
            ref_imgs.extend(re.findall(r'!\[.*?\]\((?!https?://)(.*?)\)', line))
            source_cell.append(re.sub(r'!\[(.*?)\]\((?!https?://)(.*?)\)', f'![\\1]({base_url}/\\2)', line))
        cell['source'] = source_cell
    return set(os.path.relpath(x) for x in ref_imgs)


if __name__ == '__main__':
    main()
