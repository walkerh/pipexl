"""Code for collections of generic records."""

from dataclasses import make_dataclass, astuple, replace
from dataclasses import fields as get_fields
from numbers import Number
from operator import attrgetter

from .util import normalize_name


class RecordSet(list):
    """A collection of records that are all of the same type. Constructed
    from a `list` where each item is an instance of a custom data class."""
    def __init__(self, record_type_name, fields, key_fields, tuple_iter,
                 normalize_fields=(), filters=None):
        """`key_fields` denotes the subset of field names which must have
        values in order for a record to be included. `tuple_iter` must be
        an iterable of star-compatible items, where each item has the same
        length as `fields`. `normalize_fields` has an empty default and
        denotes the subset of field whose values should be normalized."""
        self.source = None
        self.key_fields = key_fields
        self.fields = fields
        self.non_key_fields = extract_non_key_fields(fields, key_fields)
        self.normalize_fields = normalize_fields
        self.record_class = make_record_class(record_type_name, self.fields)
        record_iter = iter_records(tuple_iter, self.record_class,
                                   key_fields, normalize_fields, filters)
        super().__init__(record_iter)
        self._compute_grand_total(record_type_name)  # Sets grand_total
        self._index()  # Sets by_key

    def _compute_grand_total(self, record_type_name):
        grand_total_dict = {n: 0 for n in self.non_key_fields}
        for record in self:
            for field in list(grand_total_dict):
                value = record[field]
                if value is None:
                    value = 0
                if isinstance(value, Number):
                    grand_total_dict[field] += value
                else:  # This column is not summable.
                    del grand_total_dict[field]
        grand_total_fields = [field for field in self.non_key_fields
                              if field in grand_total_dict]
        grand_total_class = make_record_class(
            record_type_name + '_grand_total',
            grand_total_fields
        )
        self.grand_total = grand_total_class(**grand_total_dict)

    def _index(self):
        key_function = attrgetter(*self.key_fields)
        self.by_key = {key_function(record): record for record in self}


def iter_records(tuple_iter, record_class,
                 key_fields, normalize_fields, filters):
    """Generate records from an iterator of tuples. Exclude rows that are
    missing key values or are hit by `filters`."""
    filters = filters or {}
    filter_tuples = tuple((k, v) for k, v in filters.items())
    for values in tuple_iter:
        record = record_class(*values)
        valid = check_valid(record, key_fields, filter_tuples)
        if valid:
            changes = {field_name: normalize_name(record[field_name])
                       for field_name in normalize_fields}
            if changes:
                record = replace(record, **changes)
            yield record


def check_valid(record, key_fields, filter_tuples):
    """Verify that a record is not the result of a dummy row in the middle
    of a table. A dummy row will either be missing key fields or have some
    signature value in a particular field."""
    all_key_fields_filled = all(record[field] for field in key_fields)
    filters_triggered = any((record[field] == filter_value)
                            for field, filter_value in filter_tuples)
    return all_key_fields_filled and not filters_triggered


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
