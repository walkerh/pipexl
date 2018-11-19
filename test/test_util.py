import pytest

from pipexl.util import normalize_field_name


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
def test_normalize_field_name(test_input, expected):
    assert normalize_field_name(test_input) == expected
