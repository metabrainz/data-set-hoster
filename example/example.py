#!/usr/bin/env python3
import json
from datetime import datetime
from enum import Enum
from typing import List, Union, Optional
from uuid import UUID

from markupsafe import Markup
from pydantic import BaseModel

from datasethoster import Query, RequestSource, QueryOutputLine


class ExampleOutput(BaseModel):
    number: int
    num_lines: int
    x: str


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
        print(params)
        data = []
        for param in params:
            number = param.number
            for i in range(1, param.num_lines + 1):
                data.append({
                    'number': i,
                    'multiplied': i * number,
                    'option': param.x
                })
        outputs = [ExampleOutput(number=x["number"], num_lines=x["multiplied"], x=x["option"].value) for x in data]
        return outputs
