import os
import shutil

COMMON_METADATA = {
    'kernelspec': {
        'display_name': 'Python 3',
        'language': 'python',
        'name': 'python3',
    },
    'language_info': {
        'name': 'python',
    },
}

IGNORE_PATTERNS = ('.*',)


def path_iter(base_dir, ignore_patterns=IGNORE_PATTERNS):
    ignore = shutil.ignore_patterns(*ignore_patterns)
    for (dirpath, dirs, fnames) in os.walk(base_dir):
        ignored_dirs = set(ignore(dirpath, dirs))
        ignored_files = set(ignore(dirpath, fnames))
        dirs[:] = filter(lambda x: x not in ignored_dirs, dirs)
        fnames[:] = filter(lambda x: x not in ignored_files, fnames)
        for f in fnames:
            if f.endswith('.ipynb'):
                yield os.path.join(dirpath, f)


def markdown_to_ipynb(markdown_lines):
    cells = [{
        'cell_type': 'markdown',
        'metadata': {},
        'source': markdown_lines
    }]
    ipynb = {
        'cells': cells,
        'metadata': COMMON_METADATA,
        'nbformat': 4,
        'nbformat_minor': 4
    }
    return ipynb
