import unittest.mock
from unittest.mock import patch, call

import flask_testing
from flask import current_app, url_for

from datasethoster import Query
from datasethoster.main import create_app, dataset_bp, register_query, web_query_handler, json_query_handler


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
        return ['in_0', '[in_1]']

    def outputs(self):
        return ['out_0', '[out_1]']

    def fetch(self, params, count=25, offset=0):
        ret = []
        for param in params[offset:count]:
            ret.append({ 'out_0': param['in_0'], '[out_1]': param['[in_1]'] })
        return ret


class MainTestCase(flask_testing.TestCase):

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
        q = SampleQuery()
        register_query(q)
        # Re-register the blueprint to add the new urls that were added with SampleQuery
        dataset_bp.register(current_app, {}, first_registration=False)

        resp = self.client.get(url_for('dataset_hoster.test'))
        self.assert200(resp)

        resp = self.client.get(url_for('dataset_hoster.test_json'))
        self.assert400(resp)

        resp = self.client.post(url_for('dataset_hoster.test_json'), json=[])
        self.assert400(resp)

    def test_web_get(self):
        q = SampleQuery()
        register_query(q)
        params = { 'in_0':'value0', '[in_1]': 'value1,value2' }
        resp = self.client.get(url_for('dataset_hoster.test', **params))
        self.assert200(resp)

    def test_web_query_multiple(self):
        # Check that multiple items can be passed in for a field with "val1,val2"
        # and that if a value has a , in it, the field can be quoted
        q = SampleQuery()
        register_query(q)
        q.fetch = unittest.mock.Mock()
        q.fetch.return_value = [{'out_0': 'one', '[out_1]': ['two', 'three']}]

        params = { 'in_0':'value0', '[in_1]': 'value1,value2' }
        resp = self.client.get(url_for('dataset_hoster.test', **params))
        q.fetch.assert_called_with([{'in_0': 'value0', '[in_1]': 'value1'}, {'in_0': 'value0', '[in_1]': 'value2'}])

        params = { 'in_0':'value0', '[in_1]': 'value1,"value2,value3"' }
        resp = self.client.get(url_for('dataset_hoster.test', **params))
        q.fetch.assert_called_with([{'in_0': 'value0', '[in_1]': 'value1'}, {'in_0': 'value0', '[in_1]': 'value2,value3'}])

        self.assert200(resp)

    def test_json_get(self):
        q = SampleQuery()
        register_query(q)
        params = { 'in_0':'value0', '[in_1]': 'value1,value2' }
        resp = self.client.get(url_for('dataset_hoster.test_json', **params))
        self.assert200(resp)
        self.assertEqual(len(resp.json), 2)
        self.assertEqual(resp.json[0]['out_0'], 'value0')
        self.assertEqual(resp.json[0]['[out_1]'], 'value1')
        self.assertEqual(resp.json[1]['out_0'], 'value0')
        self.assertEqual(resp.json[1]['[out_1]'], 'value2')

    def test_json_post(self):
        q = SampleQuery()
        register_query(q)
        req_args = [ {
               'in_0': 'value0',
               '[in_1]': ['value1','value3']
            }, {
               'in_0': 'value1',
               '[in_1]': ['value5','value7']
            }
        ]
        resp = self.client.post(url_for('dataset_hoster.test_json'), json=req_args)
        self.assert200(resp)
        self.assertEqual(len(resp.json), 2)
        self.assertEqual(resp.json[0]['out_0'], 'value0')
        self.assertEqual(resp.json[0]['[out_1]'], ['value1', 'value3'])
        self.assertEqual(resp.json[1]['out_0'], 'value1')
        self.assertEqual(resp.json[1]['[out_1]'], ['value5', 'value7'])

    def test_json_post_offset(self):
        q = SampleQuery()
        register_query(q)
        req_args = [ {
               'in_0': 'value0',
               '[in_1]': ['value1','value3']
            }, {
               'in_0': 'value1',
               '[in_1]': ['value5','value7']
            }
        ]
        resp = self.client.post(url_for('dataset_hoster.test_json', offset=1), json=req_args)
        self.assert200(resp)
        self.assertEqual(len(resp.json), 1)
        self.assertEqual(resp.json[0]['out_0'], 'value1')
        self.assertEqual(resp.json[0]['[out_1]'], ['value5', 'value7'])

    def test_json_post_count(self):
        q = SampleQuery()
        register_query(q)
        req_args = [ {
               'in_0': 'value0',
               '[in_1]': ['value1','value3']
            }, {
               'in_0': 'value1',
               '[in_1]': ['value5','value7']
            }
        ]
        resp = self.client.post(url_for('dataset_hoster.test_json', count=1), json=req_args)
        self.assert200(resp)
        self.assertEqual(len(resp.json), 1)
        self.assertEqual(resp.json[0]['out_0'], 'value0')
        self.assertEqual(resp.json[0]['[out_1]'], ['value1', 'value3'])
