"""Code for extracting RecordSet objects from Excel worksheets."""

from pathlib import Path

from openpyxl import load_workbook

from .recordset import RecordSet
from .util import normalize_name


class InputWorkbookModel:
    """Encapsulates a list of InputTable subclasses with a naming
    pattern for the workbook. Subclasses should nest subclasses of `InputTable`
    and define the classes attribute `name_pattern` as a glob."""
    name_pattern = None  # subclasses should override

    def __init__(self, config=None):
        """The `config` parameter should contain a key matching
        `self.__class__.__name__` with the directory path to search for the
        workbook."""
        assert self.name_pattern
        config = config or {}
        directory_path = Path(config.get(self.__class__.__name__, '.'))
        hits = sorted(directory_path.glob(self.name_pattern))
        assert hits
        hit = hits[-1]  # taking the highest as most recent
        table_classes = [v for v in self.__class__.__dict__.values()
                         if isinstance(v, type) and issubclass(v, InputTable)]
        self.workbook_path = str(hit)
        workbook = load_workbook(self.workbook_path,
                                 read_only=True,
                                 data_only=True)
        for table_class in table_classes:
            table = table_class()
            setattr(self, table.name, table.load(workbook))
        workbook.close()


class InputTable:
    """A table in a worksheet. Subclasses should override class attributes
    `name`, `worksheet_name`, `table_marker`, and `key_fields` (list).
    Optional class attributes include `filters` and `header_date_format`."""
    name = worksheet_name = table_marker = filters = None
    key_fields = normalize_fields = ()
    header_date_format = '%b-%y'  # Jul-18 -> jul_18

    def __init__(self):
        assert self.name
        assert self.worksheet_name
        assert self.table_marker
        self.start_row = self.start_col = self.stop_col = None

    def load(self, workbook):
        """Load the data into a RecordSet. Set the source attribute of the
        result to self. Update start_row, start_col, and stop_col."""
        worksheet = workbook[self.worksheet_name]
        row_iter = worksheet.rows
        # Find cell with table marker.
        cell = None
        for row in row_iter:
            # Find first non-blank cell in this row.
            for cell in row:
                if cell.value:
                    break
            if cell.value == self.table_marker:
                break
        assert cell and cell.value == self.table_marker, cell
        self.start_row = cell.row + 1  # Row of first record
        # Load header.
        self.start_col = cell.column - 1
        raw_header = [n.value for n in next(row_iter)[self.start_col:]]
        limit = None
        for i, name in enumerate(raw_header):
            if name in ('', 'sep', 'separator', None):
                limit = i
                break
        if limit is None:
            limit = len(raw_header)
        converted_header = [convert_date(n, self.header_date_format)
                            for n in raw_header]
        fields = tuple(normalize_name(n)
                       for n in converted_header[:limit])
        assert set(self.key_fields) <= set(fields)
        self.stop_col = self.start_col + limit
        # Load data.
        data = RecordSet(
            self.name, fields, self.key_fields,
            iter_tuples(row_iter, self.start_col, self.stop_col),
            self.normalize_fields,
            self.filters
        )
        data.source = self
        return data


def iter_tuples(row_iter, start_col, stop_col):
    """Generate records from an Excel row iterator. Note that any row
    that is completely blank within the range `start_col:stop_col` marks
    the end of data."""
    for row in row_iter:
        values = tuple(c.value for c in row[start_col:stop_col])
        if not any(values):
            break  # end of data
        yield values


def convert_date(value, datetime_format):
    """If value has strftime (date or datetime), convert to string using
    strftime format. Otherwise return value unchanged."""
    if hasattr(value, 'strftime'):
        value = value.strftime(datetime_format)
    return value
