#!/usr/bin/env python3

# pip install -e git+https://github.com/mayhem/data-set-hoster.git#egg=datasethoster

from datasethoster import Query
from datasethoster.main import app, register_query

class ExampleQuery(Query):

    def __init__(self):
        pass

    def setup(self):
        pass

    def names(self):
        return ("example", "Useless arithmetic table example")

    def introduction(self):
        return """This is the introduction, which could provide more useful info that this introduction does."""

    def inputs(self):
        return ['number', 'num_lines', '[useless_list]']

    def outputs(self):
        return ['number', 'multiplied', "recording_mbid", "useless"]

    def fetch(self, args, offset=-1, limit=-1):
        data = []
        useless = "-".join(args['[useless_list]'])
        for i in range(1, int(args['num_lines']) + 1):
            data.append({ 'number': str(i),
                          'multiplied': str(i * int(args['number'])),
                          'recording_mbid' : '1234a7ae-2af2-4291-aa84-bd0bafe291a1',
                          'useless': useless})

        return data


if __name__ == "__main__":
    register_query(ExampleQuery())
    app.run(host="0.0.0.0", port=8001, debug=True)
