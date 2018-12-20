"""Low-level utilities or primitives."""

import re


def camel_to_snake(name):
    """Convert camelcase to snakecase. See:
    https://stackoverflow.com/a/1176023/642372"""
    sub_1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', sub_1).lower()


def normalize_name(field_name):
    """lowercase with underscores, etc"""
    fixes = (
        (r'/', '_per_'),
        (r'%', '_pct_'),
        (r'\W', '_'),
        (r'_+$', ''),
        (r'__+', '_'),
    )
    result = field_name.strip().lower() or None
    if result:
        if result.endswith('?'):
            if not re.match(r'is[_\W]', result):
                result = 'is_' + result
        for pattern, replacement in fixes:
            result = re.sub(pattern, replacement, result)
    return result
