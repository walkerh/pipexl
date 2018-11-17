"""Low-level utilities or primitives."""

def normalize_field_name(field_name):
    """lowercase with underscores, etc"""
    result = field_name or None
    if result:
        if result.endswith('?'):
            result = result[:-1]
            if not result.startswith('is_'):
                result = 'is_' + result
        result = (result.strip().lower().replace(' ', '_').replace('-', '_')
                  .replace('/', '_per_').replace('?', '_').replace('%', 'pct')
                  .replace('.', ''))
    return result
