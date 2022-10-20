#!/usr/bin/env python3

from datasethoster import Query


class ExampleQuery(Query):

    def setup(self):
        pass

    def names(self):
        return "example", "Useless arithmetic table example"

    def introduction(self):
        return """This is the introduction, which could provide more useful info that this introduction does."""

    def inputs(self):
        return ['number', 'num_lines']

    def outputs(self):
        return ['number', 'multiplied']

    def fetch(self, params, offset=-1, count=-1):
        data = []
        try:
            number = int(params[0]['number'])
        except ValueError:
            number = 1

        for param in params:
            print(param)
            for i in range(int(param['num_lines'])):
                data.append({ 'number': str(i),
                              'multiplied': str(i * number)
                            })

        return data
