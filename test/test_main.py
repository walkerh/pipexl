"""Tests for top level pipexl package."""

import pytest

from pipexl import InputTable, InputWorkbookModel
from pipexl.recordset import add_tuples


class WorkbookforTesting(InputWorkbookModel):
    """Model for book_a.xlsx"""
    name_pattern = 'book_?.xlsx'

    class InputTableForTesting(InputTable):
        """Model for the one sheet in that workbook."""
        worksheet_name = 'sheet_a'
        name = 'test_table'
        table_marker = 'test_table_marker'
        normalize_fields = (
            'value_b',
        )
        filters = dict(key_b='Total')

    class JoinInputTable(InputTable):
        """Model for a join table with more details."""
        worksheet_name = 'sheet_a'
        name = 'join_table'
        table_marker = 'join_table_marker'
        filters = dict(key_b='Total', key_c='Total')


CONFIG = dict(WorkbookforTesting='test/resources')
WORKBOOK = WorkbookforTesting(CONFIG)
TEST_RECORDS = WORKBOOK.test_table
JOIN_RECORDS = WORKBOOK.join_table
EXPECTED_KEY_A = ['agree million soon',
                  'because week were',
                  'help slowly crowd',
                  'sound rolled table',
                  'taste strange written',
                  'unit food held']
FIRST_RECORD_DICT = dict(feb_19=66.47,
                         jan_19=None,
                         key_a='unit food held',
                         key_b='Africa neighbor French',
                         value_a=79.82,
                         value_b='so_1_qp',
                         value_c=20.8)


def test_workbook_attributes():
    assert sorted(vars(WORKBOOK)) == [
        'join_table', 'test_table', 'workbook_path'
    ]


def test_table_class_name():
    assert TEST_RECORDS.record_class.__name__ == 'test_table'


def test_table_fields():
    assert set(TEST_RECORDS.fields) == set((
        'key_a', 'key_b',
        'value_a', 'value_b', 'value_c', 'jan_19', 'feb_19'
    ))


def test_join_fields():
    assert set(JOIN_RECORDS.fields) == set((
        'key_a', 'key_b', 'key_c', 'detail_a', 'detail_b'
    ))


def test_record_contents():
    r = TEST_RECORDS[0]
    assert r.fields == TEST_RECORDS.fields
    assert vars(r) == FIRST_RECORD_DICT


def test_total_records_filtered_out():
    records_with_total = [r for r in TEST_RECORDS if r.key_b == 'Total']
    for r in records_with_total:
        print(r)
    assert not records_with_total


def test_total_records_filtered_out_in_join_table():
    records_with_total = [r for r in JOIN_RECORDS
                          if 'Total' in (r.key_b, r.key_c)]
    for r in records_with_total:
        print(r)
    assert not records_with_total


def test_key_a():
    assert set(r.key_a for r in TEST_RECORDS) == set(EXPECTED_KEY_A)
    assert set(r.key_a for r in JOIN_RECORDS) == set(EXPECTED_KEY_A)


def test_has_grand_total():
    grand_total = TEST_RECORDS.grand_total
    assert grand_total.__class__.__name__ == 'test_table_grand_total'
    assert grand_total.fields == ('value_a', 'value_c', 'jan_19', 'feb_19')
    assert vars(grand_total) == pytest.approx(dict(value_a=553.80,
                                                   value_c=486.41,
                                                   jan_19=301.24,
                                                   feb_19=345.02))
    assert vars(JOIN_RECORDS.grand_total) == dict(detail_a=18,
                                                  detail_b=43)


def test_make_index():
    index = TEST_RECORDS.make_index('key_a', 'key_b')
    assert len(index) == 10
    assert sorted(index) == [
        ('agree million soon', 'silent southern receive'),
        ('because week were', 'century warm center'),
        ('because week were', 'himself shirt lake'),
        ('because week were', 'pain discover total'),
        ('because week were', 'told vowel bell'),
        ('help slowly crowd', 'Jamaica move uncle'),
        ('sound rolled table', 'steel were planet'),
        ('taste strange written', 'mile best hard'),
        ('taste strange written', 'unit each eggs'),
        ('unit food held', 'Africa neighbor French'),
    ]
    hits = index['unit food held', 'Africa neighbor French']
    assert len(hits) == 1
    r = hits[0]
    assert vars(r) == FIRST_RECORD_DICT


def test_summation_simple():
    summed = TEST_RECORDS.sum_by('key_a')
    assert summed.fields == ('key_a', 'value_a', 'value_c', 'jan_19', 'feb_19')
    index = summed.make_index('key_a')
    assert sorted(index) == [
        'agree million soon',
        'because week were',
        'help slowly crowd',
        'sound rolled table',
        'taste strange written',
        'unit food held',
    ]
    hits = index['taste strange written']
    assert len(hits) == 1
    r = hits[0]
    assert vars(r) == dict(key_a='taste strange written',
                           value_a=pytest.approx(75.17),
                           value_c=pytest.approx(87.03),
                           jan_19=pytest.approx(102.26),
                           feb_19=pytest.approx(43.59))


def test_summation_of_join_table():
    summed = JOIN_RECORDS.sum_by('key_a', 'key_b')
    assert summed.fields == ('key_a', 'key_b', 'detail_a', 'detail_b')
    index = summed.make_index('key_a', 'key_b')
    assert sorted(index) == [
        ('agree million soon', 'silent southern receive'),
        ('because week were', 'century warm center'),
        ('because week were', 'himself shirt lake'),
        ('because week were', 'pain discover total'),
        ('because week were', 'told vowel bell'),
        ('help slowly crowd', 'Jamaica move uncle'),
        ('sound rolled table', 'steel were planet'),
        ('taste strange written', 'mile best hard'),
        ('taste strange written', 'unit each eggs'),
        ('unit food held', 'Africa neighbor French'),
    ]
    hits = index[('taste strange written', 'unit each eggs')]
    assert len(hits) == 1
    r = hits[0]
    assert vars(r) == dict(key_a='taste strange written',
                           key_b='unit each eggs',
                           detail_a=3,
                           detail_b=7)


@pytest.mark.parametrize("test_input_1,test_input_2,expected", [
    ((), (), ()),  # degenerate case
    ((1,), (2,), (3,)),  # degenerate case
    ((1, 2), (2, 3), (3, 5)),  # typical case
    ((1, None), (2, None), (3, 0)),  # treat None as 0
    ((1, None), (None, 2), (1, 2)),  # treat None as 0
    ((1, None), (2,), ValueError),  # mismatched lengths
    ((1,), (2, None), ValueError),  # mismatched lengths
])
def test_add_tuples(test_input_1, test_input_2, expected):
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            add_tuples(test_input_1, test_input_2)
    else:
        assert add_tuples(test_input_1, test_input_2) == expected
