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
        return ['number', 'num_lines', '[list 0]', '[list 1]']

    def outputs(self):
        return ['number', 'multiplied', "[list]"]

    def fetch(self, args, offset=-1, limit=-1):
        data = []
        for arg in args:
            for i in range(int(arg['num_lines'])):
                data.append({ 'number': str(i),
                              'multiplied': str(i * int(arg['number'])),
                              '[list]': [arg['[list 0]'], arg['[list 1]']]
                            })

        return data


if __name__ == "__main__":
    register_query(ExampleQuery())
    app.run(host="0.0.0.0", port=8001, debug=True)
