import unittest
from typing import List

from pydantic import BaseModel
from werkzeug.datastructures import MultiDict

from datasethoster.main import convert_args_to_input, group_results


class SampleInput(BaseModel):
    artist: str
    recording_mbids: List[str]


class SampleOutputA(BaseModel):
    name: str
    count: int


class SampleOutputB(BaseModel):
    title: str


class TestConvertArgsToInput(unittest.TestCase):

    def test_scalar_field(self):
        args = MultiDict([('artist', 'Beatles')])
        params = convert_args_to_input(SampleInput, args)
        self.assertEqual(params['artist'], 'Beatles')

    def test_list_field_single_value_is_wrapped(self):
        args = MultiDict([('recording_mbids', 'abc123')])
        params = convert_args_to_input(SampleInput, args)
        self.assertEqual(params['recording_mbids'], ['abc123'])

    def test_list_field_multiple_values(self):
        args = MultiDict([('recording_mbids', 'abc'), ('recording_mbids', 'def')])
        params = convert_args_to_input(SampleInput, args)
        self.assertEqual(params['recording_mbids'], ['abc', 'def'])

    def test_unknown_field_passes_through_as_scalar(self):
        args = MultiDict([('unknown', 'value')])
        params = convert_args_to_input(SampleInput, args)
        self.assertEqual(params['unknown'], 'value')

    def test_multiple_fields(self):
        args = MultiDict([('artist', 'Beatles'), ('recording_mbids', 'abc'), ('recording_mbids', 'def')])
        params = convert_args_to_input(SampleInput, args)
        self.assertEqual(params['artist'], 'Beatles')
        self.assertEqual(params['recording_mbids'], ['abc', 'def'])


class TestGroupResults(unittest.TestCase):

    def test_empty(self):
        self.assertEqual(group_results([]), [])

    def test_single_type(self):
        results = [SampleOutputA(name='x', count=1), SampleOutputA(name='y', count=2)]
        groups = group_results(results)
        self.assertEqual(len(groups), 1)
        keys, items = groups[0]
        self.assertEqual(list(keys), ['name', 'count'])
        self.assertEqual(len(items), 2)

    def test_mixed_types_creates_two_groups(self):
        results = [
            SampleOutputA(name='x', count=1),
            SampleOutputB(title='t'),
        ]
        groups = group_results(results)
        self.assertEqual(len(groups), 2)
        keys_a, items_a = groups[0]
        keys_b, items_b = groups[1]
        self.assertEqual(list(keys_a), ['name', 'count'])
        self.assertEqual(list(keys_b), ['title'])

    def test_interleaved_types_creates_multiple_groups(self):
        results = [
            SampleOutputA(name='a', count=1),
            SampleOutputA(name='b', count=2),
            SampleOutputB(title='t1'),
            SampleOutputA(name='c', count=3),
        ]
        groups = group_results(results)
        self.assertEqual(len(groups), 3)
        self.assertEqual(len(groups[0][1]), 2)
        self.assertEqual(len(groups[1][1]), 1)
        self.assertEqual(len(groups[2][1]), 1)
