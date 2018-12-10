"""Tests for top level pipexl package."""

import pytest

from pipexl import Table, WorkbookModel


class WorkbookforTesting(WorkbookModel):
    """Model for book_a.xlsx"""
    name_pattern = 'book_?.xlsx'
    class TableForTesting(Table):
        """Model for the one sheet in that workbook."""
        worksheet_name = 'sheet_a'
        name = 'test_table'
        table_marker = 'table_marker'
        key_fields = (
            'key_a',
            'key_b',
        )
        normalize_fields = (
            'value_b',
        )
        filters = dict(key_b='Total')


CONFIG = dict(WorkbookforTesting='test/resources')
WORKBOOK = WorkbookforTesting(CONFIG)
TEST_RECORDS = WORKBOOK.test_table
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
        'test_table', 'workbook_path'
    ]


def test_table_class_name():
    assert TEST_RECORDS.record_class.__name__ == 'test_table'


def test_table_fields():
    assert TEST_RECORDS.key_fields == ('key_a', 'key_b')
    assert TEST_RECORDS.non_key_fields == (
        'value_a', 'value_b', 'value_c', 'jan_19', 'feb_19'
    )
    assert set(TEST_RECORDS.fields) == set(TEST_RECORDS.key_fields +
                                           TEST_RECORDS.non_key_fields)


def test_record_contents():
    r = TEST_RECORDS[0]
    assert r.fields == TEST_RECORDS.fields
    assert vars(r) == FIRST_RECORD_DICT


def test_total_records_filtered_out():
    records_with_total = [r for r in TEST_RECORDS if r.key_b == 'Total']
    for r in records_with_total:
        print(r)
    assert not records_with_total


def test_key_a():
    assert set(r.key_a for r in TEST_RECORDS) == set(EXPECTED_KEY_A)


def test_has_grand_total():
    grand_total = TEST_RECORDS.grand_total
    assert grand_total.fields == ('value_a', 'value_c', 'jan_19', 'feb_19')
    assert vars(grand_total) == pytest.approx(dict(value_a=553.80,
                                                   value_c=486.41,
                                                   jan_19=301.24,
                                                   feb_19=345.02))
