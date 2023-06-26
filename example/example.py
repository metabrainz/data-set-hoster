#!/usr/bin/env python3
from typing import List, Union

from pydantic import BaseModel

from datasethoster import Query


class ExampleInput(BaseModel):
    number: int
    num_lines: int


class ExampleOutput(BaseModel):
    number1: int
    multiplied: int


class ExampleQuery(Query[ExampleInput, ExampleOutput]):

    def setup(self):
        pass

    def names(self):
        return "example", "Useless arithmetic table example"

    def introduction(self):
        return """This is the introduction, which could provide more useful info that this introduction does."""

    def inputs(self):
        return ExampleInput

    def outputs(self):
        return ExampleOutput

    def fetch(self, params: List[ExampleInput], offset=-1, count=-1) -> List[ExampleOutput]:
        print(params)
        data = []
        for param in params:
            number = param.number
            for i in range(1, param.num_lines + 1):
                data.append({
                    'number': i,
                    'multiplied': i * number
                })
        outputs = [ExampleOutput(number1=x["number"], multiplied=x["multiplied"]) for x in data]
        return outputs
