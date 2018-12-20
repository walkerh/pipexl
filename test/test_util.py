"""Tests for pipexl.util."""

import pytest

from pipexl.util import camel_to_snake, normalize_name


@pytest.mark.parametrize("test_input,expected", [
    ('camel_case', 'camel_case'),
    ('CamelCase', 'camel_case'),
    ('CamelCamelCase', 'camel_camel_case'),
    ('Camel2Camel2Case', 'camel2_camel2_case'),
    ('getHTTPResponseCode', 'get_http_response_code'),
    ('get2HTTPResponseCode', 'get2_http_response_code'),
    ('HTTPResponseCode', 'http_response_code'),
    ('HTTPResponseCodeXYZ', 'http_response_code_xyz'),
])
def test_camel_to_snake(test_input, expected):
    """Parameterized test for the various normalization cases. Everything
    should evaluate to a legal Python name."""
    assert camel_to_snake(test_input) == expected


@pytest.mark.parametrize("test_input,expected", [
    ('foo bar-baz', 'foo_bar_baz'),
    ('foo.bar\nbaz', 'foo_bar_baz'),
    ('foo.bar.baz', 'foo_bar_baz'),
    ('foo bar [baz]', 'foo_bar_baz'),
    ('foo bar (baz)', 'foo_bar_baz'),
    ('foo _ bar _(baz)_', 'foo_bar_baz'),
    ('foo _ bar (_baz)_', 'foo_bar_baz'),
    ('foo BAR (baz)', 'foo_bar_baz'),
    ('foo bar(baz)', 'foo_bar_baz'),
    ('foo/bar(baz)', 'foo_per_bar_baz'),
    ('foo / -bar(baz)', 'foo_per_bar_baz'),
    ('foo bar % (baz)', 'foo_bar_pct_baz'),
    ('foo bar (baz)%', 'foo_bar_baz_pct'),
    ('foo bar (baz)?', 'is_foo_bar_baz'),
    ('island bar (baz)', 'island_bar_baz'),
    ('island bar (baz)?', 'is_island_bar_baz'),
    ('is island bar (baz)?', 'is_island_bar_baz'),
    ('is.island bar (baz)?', 'is_island_bar_baz'),
    ('is-island bar (baz)?', 'is_island_bar_baz'),
    ('is_island bar (baz)?', 'is_island_bar_baz'),
    ('is_ _island bar (baz)?', 'is_island_bar_baz'),
])
def test_normalize_name(test_input, expected):
    """Parameterized test for the various normalization cases. Everything
    should evaluate to a legal Python name."""
    assert normalize_name(test_input) == expected
