import unittest.mock
from typing import List
from unittest.mock import patch, call

import flask_testing
from flask import current_app, url_for
from pydantic import BaseModel

from datasethoster import Query, RequestSource
from datasethoster.main import (
    DEFAULT_QUERY_RESULT_SIZE,
    create_app,
    dataset_bp,
    register_query,
    web_query_handler,
    json_query_handler,
)


class SampleInputModel(BaseModel):
    in_0: str
    in_1: List[str]


class SampleOutputModel(BaseModel):
    out_0: str
    out_1: List[str]


class SampleQuery(Query):

    def __init__(self):
        Query.__init__(self)

    def setup(self):
        pass

    def names(self):
        return ("test", "test-endpoint")

    def introduction(self):
        return "intro"

    def inputs(self):
        return SampleInputModel

    def outputs(self):
        return SampleOutputModel

    def fetch(self, params, source, offset=0, count=DEFAULT_QUERY_RESULT_SIZE):
        if count == -1:
            count = DEFAULT_QUERY_RESULT_SIZE
        ret = []
        for param in params[offset:offset + count]:
            ret.append(SampleOutputModel(out_0=param.in_0, out_1=param.in_1))
        return ret


class MainTestCase(flask_testing.TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Register queries before any app is created so URL rules are added
        # to the blueprint's deferred queue (Flask 3.x requirement).
        register_query(SampleQuery())

    def create_app(self):
        return create_app()

    def setUp(self):
        flask_testing.TestCase.setUp(self)

    def tearDown(self):
        flask_testing.TestCase.tearDown(self)

    @patch('datasethoster.main.dataset_bp.add_url_rule')
    def test_register_query(self, add):
        q = SampleQuery()
        register_query(q)
        calls = [call("/test", "test", web_query_handler),
                 call("/test/json", "test_json", json_query_handler, methods=['GET', 'POST', 'OPTIONS'])]
        add.assert_has_calls(calls)

    def test_index_page(self):
        resp = self.client.get(url_for('dataset_hoster.index'))
        self.assert200(resp)

    def test_nonexistant_page(self):
        resp = self.client.get("bad")
        self.assert404(resp)

    def test_empty_query_page(self):
        resp = self.client.get(url_for('dataset_hoster.test'))
        self.assert200(resp)

        # GET without required args → 400
        resp = self.client.get(url_for('dataset_hoster.test_json'))
        self.assert400(resp)

        # POST with empty list → 200 with empty result
        resp = self.client.post(url_for('dataset_hoster.test_json'), json=[])
        self.assert200(resp)
        self.assertEqual(resp.json, [])

    def test_web_get(self):
        params = {'in_0': 'value0', 'in_1': 'value1'}
        resp = self.client.get(url_for('dataset_hoster.test', **params))
        self.assert200(resp)

    def test_json_get(self):
        params = {'in_0': 'value0', 'in_1': 'value1'}
        resp = self.client.get(url_for('dataset_hoster.test_json', **params))
        self.assert200(resp)
        self.assertEqual(len(resp.json), 1)
        self.assertEqual(resp.json[0]['out_0'], 'value0')
        self.assertEqual(resp.json[0]['out_1'], ['value1'])

    def test_json_post(self):
        req_args = [
            {'in_0': 'value0', 'in_1': ['value1', 'value3']},
            {'in_0': 'value1', 'in_1': ['value5', 'value7']},
        ]
        resp = self.client.post(url_for('dataset_hoster.test_json'), json=req_args)
        self.assert200(resp)
        self.assertEqual(len(resp.json), 2)
        self.assertEqual(resp.json[0]['out_0'], 'value0')
        self.assertEqual(resp.json[0]['out_1'], ['value1', 'value3'])
        self.assertEqual(resp.json[1]['out_0'], 'value1')
        self.assertEqual(resp.json[1]['out_1'], ['value5', 'value7'])

    def test_json_post_offset(self):
        req_args = [
            {'in_0': 'value0', 'in_1': ['value1', 'value3']},
            {'in_0': 'value1', 'in_1': ['value5', 'value7']},
        ]
        resp = self.client.post(url_for('dataset_hoster.test_json', offset=1), json=req_args)
        self.assert200(resp)
        self.assertEqual(len(resp.json), 1)
        self.assertEqual(resp.json[0]['out_0'], 'value1')
        self.assertEqual(resp.json[0]['out_1'], ['value5', 'value7'])

    def test_json_post_count(self):
        req_args = [
            {'in_0': 'value0', 'in_1': ['value1', 'value3']},
            {'in_0': 'value1', 'in_1': ['value5', 'value7']},
        ]
        resp = self.client.post(url_for('dataset_hoster.test_json', count=1), json=req_args)
        self.assert200(resp)
        self.assertEqual(len(resp.json), 1)
        self.assertEqual(resp.json[0]['out_0'], 'value0')
        self.assertEqual(resp.json[0]['out_1'], ['value1', 'value3'])
