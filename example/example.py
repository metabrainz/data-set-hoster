#!/usr/bin/env python3
from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel

from datasethoster import Query


class ExampleOutput(BaseModel):
    number: int
    multiplied: int


class ExampleInput2(BaseModel):
    number: list[int]
    multiplied: int


class ExampleOutput2(BaseModel):
    number: int
    added: int


class ExampleQuery(Query[BaseModel, ExampleOutput]):

    def setup(self):
        pass

    def names(self):
        return "example", "Useless arithmetic table example"

    def introduction(self):
        return """This is the introduction, which could provide more useful info that this introduction does."""

    def inputs(self):
        X = Enum("X", {"foo": "foo", "bar": "bar"})

        class ExampleInput(BaseModel):
            number: int
            num_lines: int
            x: X

        return ExampleInput

    def outputs(self):
        return ExampleOutput

    def fetch(self, params: list, source, offset=-1, count=-1) -> List[ExampleOutput]:
        data = []
        for param in params:
            number = param.number
            for i in range(1, param.num_lines + 1):
                data.append({
                    'number': i,
                    'multiplied': i * number,
                    'option': param.x
                })
        outputs = [ExampleOutput(number=x["number"], multiplied=x["multiplied"]) for x in data]
        return outputs


class ExampleQuery2(Query[ExampleInput2, ExampleOutput2]):

    def setup(self):
        pass

    def names(self):
        return "example-2", "Useless arithmetic addition example"

    def introduction(self):
        return """This is the introduction, which could provide more useful info that this introduction does."""

    def inputs(self):
        return ExampleInput2

    def outputs(self):
        return ExampleOutput

    def fetch(self, params: List[ExampleInput2], source, offset=-1, count=-1) -> List[ExampleOutput2]:
        data = []
        for param in params:
            for number in param.number:
                for i in range(1, param.multiplied + 1):
                    data.append({
                        'number': i,
                        'added': i + number
                    })
        outputs = [ExampleOutput2(number=x["number"], added=x["added"]) for x in data]
        return outputs
