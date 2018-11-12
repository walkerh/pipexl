"""Code for constructing data pipelines that involve tables inside
workbooks."""


from dataclasses import make_dataclass, fields, astuple
from pathlib import Path


from openpyxl import load_workbook


class WorkbookModel:
    """Encapsulates a list of Table subclasses with a naming
    pattern for the workbook. Subclasses should nest subclasses of `Table` and
    define the classes attribute `name_pattern` as a glob."""
    name_pattern = None  # subclasses should override

    def __init__(self, config=None):
        """The `config` parameter should contain a key matching
        `self.__class__.__name__` with the directory path to search for the
        workbook."""
        config = config or {}
        directory_path = Path(config.get(self.__class__.__name__, '.'))
        hits = sorted(directory_path.glob(self.name_pattern))
        assert hits
        hit = hits[-1]  # taking the highest as most recent
        table_classes = [v for v in self.__class__.__dict__.values()
                         if isinstance(v, type) and issubclass(v, Table)]
        self.workbook_path = str(hit)
        self.workbook = load_workbook(self.workbook_path,
                                      read_only=True,
                                      data_only=True)
        self.tables = []
        for table_class in table_classes:
            table = table_class(self.workbook)
            self.tables.append(table)
            setattr(self, table.name, table)


class Table:
    """A table in a worksheet. Subclasses should override class attributes
    `name`, `worksheet_name`, `table_marker`, and `key_fields` (list)."""
    def __init__(self, workbook):
        self.worksheet = workbook[self.worksheet_name]
        row_iter = self.worksheet.rows
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
        self.fields = tuple(normalize_field_name(n)
                            for n in raw_header[:limit])
        self.non_key_fields = tuple(set(self.fields) - set(self.key_fields))
        # Define record class.
        self.stop_col = self.start_col + limit
        self.record_class = make_record_class(self.name, self.fields)
        # Load data.
        self.data = list(iter_records(
            row_iter, self.start_col, self.stop_col,
            self.record_class, self.key_fields
        ))


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


def iter_records(row_iter, start_col, stop_col, record_class, key_fields):
    """Generate records from an Excel row iterator. Exclude rows that are
    missing key values."""
    for row in row_iter:
        values = tuple(c.value for c in row[start_col:stop_col])
        record = record_class(*values)
        valid = all(record[field] for field in key_fields)
        if valid:
            yield record


def make_record_class(cls_name, fields):
    """Return a class for holding table rows as records. The data can be
    accessed using either attribute or dictionary syntax."""
    return make_dataclass(cls_name,
                          fields,
                          bases=(RecordAttributeMixin,),
                          frozen=True)


class RecordAttributeMixin:
    """Mixin class adds record methods to generated dataclass."""
    astuple = property(astuple)

    @property
    def fields(self):
        return tuple(f.name for f in fields(self))

    def __getitem__(self, name):
        return self.__dict__[name]
