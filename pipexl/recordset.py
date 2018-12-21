"""Code for collections of generic records."""

from collections import defaultdict
from dataclasses import make_dataclass, astuple, replace
from dataclasses import fields as get_fields
from numbers import Number
from operator import attrgetter

from .util import normalize_name


class RecordSet(list):
    """A collection of records that are all of the same type. Constructed
    from a `list` where each item is an instance of a custom data class."""
    def __init__(self, record_type_name, fields, tuple_iter,
                 normalize_fields=(), filters=None):
        """`tuple_iter` must be an iterable of star-compatible items, where
        each item has the same length as `fields`. `normalize_fields` has an
        empty default and denotes the subset of field whose values should be
        normalized."""
        self.source = None
        self.fields = fields
        self.normalize_fields = normalize_fields
        self.record_class = make_record_class(record_type_name, self.fields)
        record_iter = iter_records(tuple_iter, self.record_class,
                                   normalize_fields, filters)
        super().__init__(record_iter)
        self._compute_grand_total()  # Sets grand_total

    def sum_by(self, *key_fields):
        """Aggregate by the specified key fields, returting a new RecordSet
        of the corresponding subtotals"""
        result_class_name = (self.record_class.__name__
                             + '_by_' + '_'.join(key_fields))
        summed_fields = self.grand_total.fields
        fields = key_fields + summed_fields
        key_function = make_key_function(key_fields)
        data_function = make_key_function(summed_fields)
        aggregation = aggregate(self, key_function, data_function)
        tuples = sorted(key + value for key, value in aggregation.items())
        return self.__class__(result_class_name, fields, tuples)

    def _compute_grand_total(self):
        record_type_name = self.record_class.__name__
        grand_total_dict = {n: 0 for n in self.fields}
        for record in self:
            for field in list(grand_total_dict):
                value = record[field]
                if value is None:
                    value = 0
                if isinstance(value, Number):
                    grand_total_dict[field] += value
                else:  # This column is not summable.
                    del grand_total_dict[field]
        grand_total_fields = [field for field in self.fields
                              if field in grand_total_dict]
        grand_total_class = make_record_class(
            record_type_name + '_grand_total',
            grand_total_fields
        )
        self.grand_total = grand_total_class(**grand_total_dict)

    def make_index(self, *key_fields):
        key_function = attrgetter(*key_fields)
        result = defaultdict(list)
        for record in self:
            result[key_function(record)].append(record)
        return result


def iter_records(tuple_iter, record_class, normalize_fields, filters):
    """Generate records from an iterator of tuples. Exclude rows that are
    missing key values or are hit by `filters`."""
    filters = filters or {}
    filter_tuples = tuple((k, v) for k, v in filters.items())
    for values in tuple_iter:
        record = record_class(*values)
        valid = check_valid(record, filter_tuples)
        if valid:
            changes = {field_name: normalize_name(record[field_name])
                       for field_name in normalize_fields}
            if changes:
                record = replace(record, **changes)
            yield record


def check_valid(record, filter_tuples):
    """Verify that a record is not the result of a dummy row in the middle
    of a table. A dummy row will either be missing key fields or have some
    signature value in a particular field."""
    filters_triggered = any((record[field] == filter_value)
                            for field, filter_value in filter_tuples)
    return not filters_triggered


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


def make_key_function(attributes):
    """Given a tuple of attribute names. Return a key function that converts
    objects to tuples of values. This is similar to operator.attrgetter,
    except that the result is always a tuple even for a single attribute."""
    getter = attrgetter(*attributes)
    if len(attributes) > 1:
        result = getter
    else:
        def result(instance):
            return (getter(instance),)
    return result


def aggregate(objects, key_function, data_function):
    """Return a dict mapping keys to subtotals. Both keys and data must be
    tuples."""
    result = {}
    for item in objects:
        key = key_function(item)
        data = data_function(item)
        if key not in result:
            result[key] = (0,) * len(data)
        result[key] = add_tuples(result[key], data)
    return result


def add_tuples(tuple_1, tuple_2):
    """Assuming the tuples of the same length and contain numbers. Create a new
    tuple that is the result of pairwise addition."""
    if len(tuple_1) != len(tuple_2):
        raise ValueError(f'different lengths for {tuple_1} and {tuple_2}')
    result = []
    for item_1, item_2 in zip(tuple_1, tuple_2):
        number_1 = 0 if item_1 is None else item_1
        number_2 = 0 if item_2 is None else item_2
        result.append(number_1 + number_2)
    return tuple(result)
