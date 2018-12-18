# Connect to the technology we will be using:
from pipexl import (InputWorkbookModel, InputTable,
                    OutputWorkbookModel, OutputTable,
                    find_duplicates, load_config)

# Define the important columns.
key_columns = ('key_1', 'key_2', 'key_3')  # First two shared between two tables
types = ('type_x', 'type_y')
months = tuple('jan_19 feb_19'.split())  # All of the headers for months

# Define the input and output workbooks, worksheets and tables.
class ExampleInputWorkbook(InputWorkbookModel):
    name_pattern = 'input_book_?.xlsx'
    class table_a(InputTable):
        worksheet_name = 'input_sheet'
        table_marker = 'table_a_marker'
        required_fields = key_columns[:2] + months
    class table_b(InputTable):
        worksheet_name = 'input_sheet'
        table_marker = 'table_b_marker'
        required_fields = key_columns + types

class ExampleOutputWorkbook(OutputWorkbookModel):
    name_pattern = 'output_book_{num:<03}.xlsx'
    class results(OutputTable):
        worksheet_name = 'output_sheet'
        fields = ('type',) + key_columns[:2] + months

# Define the directories containing the workbooks.
# This information comes from an external file.
config = load_config()

# Load the input data.
input_workbook = ExampleInputWorkbook(config)

# Some convenience variables:
table_a = input_workbook.table_a
table_b = input_workbook.table_b

# key_getter is a function that converts a record to the tuple of values of the
# first two key columns: record -> (key_1_value, key_2_value)
key_getter = attrgetter(*key_columns[:2])

# Make a note of the combinations of keys used in both tables.
table_a_keys = tuple(key_getter(record) for record in table_a)
table_b_keys = tuple(key_getter(record) for record in table_b)

# Define the empty output workbook.
# An output workbook records metadata about the input sources and also
# any errors or warnings.
with ExampleOutputWorkbook(config, table_a, table_b) as output_workbook:
    # Verify that each key (conmbination) in table A is unique.
    duplicate_keys = find_duplicates(table_a_keys)
    if duplicate_keys:
        output_workbook.record_error(
            f'duplicate keys in table_a: {duplicate_keys}'
        )
        # There will be "duplicate" rows in the output. These rows will have
        # the same key combinations but may possess different month values.

    # Verify that the keys in table A are a subset of table B.
    bad_keys = set(table_a_keys) - set(table_b_keys)
    if bad_keys:
        output_workbook.fail(f'extra keys in table_a: {sorted(bad_keys)}')
        # Processing stops here.
        # An alternative approach would be to delete the bad keys and keep
        # going. To enable this code, remove the line right above these
        # comments (the line that says "fail").
        output_workbook.record_error(
            f'extra keys in table_a: {sorted(bad_keys)}'
        )
        table_a_keys = tuple(key for key in table_a_keys
                             if key not in bad_keys)

    # Check for keys in table B that are not used in table A:
    unused_keys = set(table_b_keys) - set(table_a_keys)
    if unused_keys:
        output_workbook.record_warning(
            f'extra keys in table_a: {sorted(unused_keys)}'
        )
        # Those key combinations will not appear in the final output.

    # Rollup table B by the first two keys, ignoring the third.
    table_b_subtotals = table_b.sum_by(*key_fields[:2])

    # Combine the rollup from table B with table A.
    for table_a_record in table_a:
        key_1, key_2 = key_getter(table_a_record)
        table_b_subtotal = table_b_subtotals[key_1, key_2]
        # Each type column results in a separate row in the output table.
        # Each output row is marked with a code representing the originating
        # type column.
        for type_name in types:
            new_row_values = (type_name, key_1, key_2) + tuple(
                table_b_subtotal[type_name] * table_a_record[month]
                for month in months
            )
            output_workbook.results.add_tuple(new_row_values)
