#! /usr/bin/env python3

import argparse
import os
import zipfile
import shutil

from nbsphinx_normalizer import sanitize_ipynb
from colabizer import colabize_directory

IGNORE_PATTERNS = ( '.*', '*~', '__pycache__')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', required=True, help='Specify a path to a source directory.')
    parser.add_argument('-z', '--zip', metavar='DEST', help=f'Generate release zip into a specified destination.')
    parser.add_argument('-r', '--repository', default='.', help=f'Specify a path to a local repository to host Colab notebooks (default: the current directory).')
    parser.add_argument('-g', '--github', metavar=('usrename', 'reponame', 'branch', 'colab_dir'), nargs=4, help=f'Specify the information of GitHub repository (default: the current directory).')
    parser.add_argument('-x', '--nbsphinx', metavar='DEST_DIR', help=f'Generate source for nbsphinx to specified destination.')
    commandline_args = parser.parse_args()

    assert os.path.exists(commandline_args.source)
    assert os.path.isdir(commandline_args.source)
    if commandline_args.zip is not None:
        generate_zip(commandline_args.source, commandline_args.zip)
    if commandline_args.github is not None:
        generate_colab(commandline_args.source, commandline_args.repository, *commandline_args.github)
    if commandline_args.nbsphinx is not None:
        generate_nbsphinx_src(commandline_args.source, commandline_args.nbsphinx)


def generate_zip(source_dir, dest):
    source_dir = os.path.relpath(source_dir)
    ignore = shutil.ignore_patterns(*IGNORE_PATTERNS)
    with zipfile.ZipFile(dest, 'w') as zipf:
        for (dirpath, dirs, fnames) in os.walk(source_dir):
            ignored_dirs = set(ignore(dirpath, dirs))
            ignored_files = set(ignore(dirpath, fnames))
            dirs[:] = filter(lambda x: x not in ignored_dirs, dirs)
            fnames[:] = filter(lambda x: x not in ignored_files, fnames)
            for f in fnames:
                fullpath = os.path.join(dirpath, f)
                zipf.write(fullpath, os.path.relpath(fullpath, source_dir))

        print(f'{zipf.filename} archived:')
        for fn in zipf.namelist():
            print('  -', fn)


def generate_colab(source_dir, repo_dir, github_username, github_reponame, github_branch, colab_dir):
    url_base = f'https://raw.githubusercontent.com/{github_username}/{github_reponame}/{github_branch}/{colab_dir}'
    dest_base = os.path.relpath(os.path.join(repo_dir, colab_dir), source_dir)
    orig_dir = os.getcwd()
    os.chdir(source_dir)
    colabize_directory('.', dest_base, dest_base, url_base, IGNORE_PATTERNS)
    os.chdir(orig_dir)


def generate_nbsphinx_src(source_dir, dest_dir):
    os.makedirs(dest_dir)
    shutil.copytree(source_dir, dest_dir, ignore=shutil.ignore_patterns(*IGNORE_PATTERNS), dirs_exist_ok=True)
    for basedir, _, fnames in os.walk(dest_dir):
        for fname in fnames:
            if fname.endswith('.ipynb'):
                path = os.path.join(basedir, fname)
                sanitize_ipynb(path, path)


if __name__ == '__main__':
    main()
