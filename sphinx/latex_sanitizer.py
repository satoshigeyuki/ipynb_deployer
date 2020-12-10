#! /usr/bin/env python3

import sys

CRITICAL_CHARACTER_MAPPING = {
    '▷': r'$\triangleright$',
}


def sanitize_latex(source, dest):
    with open(source, encoding='utf-8') as f:
        latex = f.read()
    with open(dest, mode='w', encoding='utf-8') as f:
        f.write(''.join(CRITICAL_CHARACTER_MAPPING.get(c, c) for c in latex))


if __name__ == '__main__':
    for filepath in sys.argv[1:]:
        assert filepath.endswith('.tex')
        sanitize_latex(filepath, filepath)
