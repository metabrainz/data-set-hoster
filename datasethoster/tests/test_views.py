import os
import unittest
from unittest.mock import patch, call

import flask_testing
from flask import url_for

from datasethoster import Query
from datasethoster.main import register_query, convert_http_args_to_json, error_check_arguments, create_app as main_create_app, \
                               web_query_handler, json_query_handler

class TestQuery(Query):

    def __init__(self):
        Query.__init__(self)

    def setup(self):
        pass

    def names(self):
        return ("test", "test-endpoint")

    def introduction(self):
        return "intro"

    def intputs(self):
        return ['field_0', '[field_1]']

    def outputs(self):
        return ['out_0', '[out_1]']

    def fetch(self, params, count, offset):
        return 

class MainTestCase(flask_testing.TestCase):

    def create_app(self):
        return main_create_app(True)

    def setUp(self):
        flask_testing.TestCase.setUp(self)

    def tearDown(self):
        flask_testing.TestCase.tearDown(self)

    @patch('datasethoster.main.app.add_url_rule')
    def test_register_query(self, add):

        q = TestQuery()
        register_query(q)
        calls = [call("/test", "test", web_query_handler), 
                 call("/test/json", "test_json", json_query_handler, methods=['GET', 'POST'])]
        add.assert_has_calls(calls)

    def test_index_page(self):
        resp = self.client.get(url_for('.index'))
        self.assert200(resp)
