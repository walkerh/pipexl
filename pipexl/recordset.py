"""Code for collections of generic records."""

from dataclasses import make_dataclass, astuple
from dataclasses import fields as get_fields


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
