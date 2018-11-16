"""Code for constructing data pipelines that involve tables inside
workbooks."""


from dataclasses import make_dataclass, astuple
from dataclasses import fields as get_fields
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
        assert self.name_pattern
        config = config or {}
        directory_path = Path(config.get(self.__class__.__name__, '.'))
        hits = sorted(directory_path.glob(self.name_pattern))
        assert hits
        hit = hits[-1]  # taking the highest as most recent
        table_classes = [v for v in self.__class__.__dict__.values()
                         if isinstance(v, type) and issubclass(v, Table)]
        self.workbook_path = str(hit)
        workbook = load_workbook(self.workbook_path,
                                 read_only=True,
                                 data_only=True)
        for table_class in table_classes:
            table = table_class()
            setattr(self, table.name, table.load(workbook))
        workbook.close()


class Table:
    """A table in a worksheet. Subclasses should override class attributes
    `name`, `worksheet_name`, `table_marker`, and `key_fields` (list)."""
    name = worksheet_name = table_marker = None
    key_fields = ()

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
        fields = tuple(normalize_field_name(n)
                       for n in raw_header[:limit])
        assert set(self.key_fields) <= set(fields)
        self.stop_col = self.start_col + limit
        # Load data.
        data = RecordSet(
            self.name, fields, self.key_fields,
            iter_tuples(row_iter, self.start_col, self.stop_col)
        )
        data.source = self
        return data


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


class RecordSet(list):
    """A collection of records that are all of the same type. Constructed
    from """
    def __init__(self, record_type_name, fields, key_fields, tuple_iter):
        self.source = None
        self.key_fields = key_fields
        self.fields = fields
        self.non_key_fields = extract_non_key_fields(fields, key_fields)
        self.record_class = make_record_class(record_type_name, self.fields)
        record_iter = iter_records(tuple_iter, self.record_class, key_fields)
        super().__init__(record_iter)


def iter_records(tuple_iter, record_class, key_fields):
    """Generate records from an iterator of tuples. Exclude rows that are
    missing key values."""
    for values in tuple_iter:
        record = record_class(*values)
        valid = all(record[field] for field in key_fields)
        if valid:
            yield record


def iter_tuples(row_iter, start_col, stop_col):
    """Generate records from an Excel row iterator."""
    for row in row_iter:
        yield tuple(c.value for c in row[start_col:stop_col])


def make_record_class(cls_name, field_names):
    """Return a class for holding table rows as records. The data can be
    accessed using either attribute or dictionary syntax."""
    return make_dataclass(cls_name,
                          field_names,
                          bases=(RecordAttributeMixin,),
                          frozen=True)


class RecordAttributeMixin:
    """Mixin class adds record methods to generated dataclass."""
    astuple = property(astuple)

    @property
    def fields(self):
        """Return `tuple` of the field names."""
        return tuple(f.name for f in get_fields(self))

    def __getitem__(self, name):
        return self.__dict__[name]


def extract_non_key_fields(fields, key_fields):
    """Returns `non_key_fields` which preserves the order in `fields`."""
    return tuple(f for f in fields if f not in key_fields)
