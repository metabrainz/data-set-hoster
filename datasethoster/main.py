from collections import defaultdict
import copy
import traceback

from flask import Flask, render_template, request, jsonify
from werkzeug.exceptions import NotFound, BadRequest, InternalServerError



registered_queries = {}

TEMPLATE_FOLDER = "template"

app = Flask(__name__,
            template_folder = TEMPLATE_FOLDER)


@app.route('/')
def index():

    return render_template("index.html", queries=registered_queries)


def web_query_handler():
    slug = request.path[1:]
    try:
        query = registered_queries[slug]
    except KeyError:
        raise NotFound

    slug, desc = query.names()
    introduction = query.introduction()
    inputs = query.inputs()
    columns = query.outputs()
    args = {}
    data = None
    error = None
    try:
        for input in inputs:
            args[input] = request.args[input]
            # Is the query expecting a list? Check the name of the argument
            # and see if we need to parse the comma seperated arguments into a list
            if input[0] == '[' and input[-1] == ']':
                args[input] = args[input].split(",")

        print(args)
        try:
            data = query.fetch(args)
        except Exception as err:
            data = None
            error = traceback.format_exc()

    except KeyError:
        pass

    for input in inputs:
        if input[0] == '[' and input[-1] == ']':
            try:
                args[input] = ",".join(args[input])
            except KeyError:
                pass

    json_url = request.url.replace(slug, slug + "/json")
    return render_template("query.html",
                           error=error,
                           data=data,
                           inputs=inputs,
                           columns=columns,
                           introduction=introduction,
                           args=args,
                           desc=desc,
                           slug=slug,
                           json_url=json_url)


def json_query_handler_get():
    if request.method == 'POST':
        return json_query_handler_post()

    slug, _ = request.path[1:].split("/")
    try:
        query = registered_queries[slug]
    except KeyError:
        raise NotFound

    slug, desc = query.names()
    inputs = query.inputs()
    columns = query.outputs()
    args = {}
    for input in inputs:
        try:
            args[input] = request.args[input]
        except KeyError:
            raise BadRequest("Required argument %s missing." % input)
        if not args[input]:
            raise BadRequest("Required argument %s cannot be blank." % input)

        # Is the query expecting a list? Check the name of the argument
        # and see if we need to parse the comma seperated arguments into a list
        if input[0] == '[' and input[-1] == ']':
            args[input] = args[input].split(",")

    try:
        data = query.fetch(args)
    except Exception as err:
        print(traceback.format_exc())
        return jsonify({}), 500
        
    return jsonify(data)

def fetch_query(url):
    slug, _ = url[1:].split("/")
    try:
        query = registered_queries[slug]
    except KeyError:
        raise NotFound

    return query

def json_query_handler_post():

    if not isinstance(request.json, list):
        raise BadRequest("POST data must be a JSON list of hashes.")

    query = fetch_query(request.path)
    inputs = query.inputs()
    outputs = query.outputs()

    args = copy.deepcopy(request.json)
    for i, row in enumerate(request.json):
        for input in inputs:
            if not input in row:
                raise BadRequest("Required argument %s missing in row %d." % (input, i))
            if not row[input]:
                raise BadRequest("Required argument %s cannot be blank." % (input, i))

            if input[0] == '[' and input[-1] == ']':
                args[i][input] = row[input].split(",")

    try:
        data = query.fetch(request.json)
    except Exception as err:
        print(traceback.format_exc())
        return jsonify({}), 500
        
    return jsonify(data)

def register_query(query):

    slug, name = query.names()
    registered_queries[slug] = query
    app.add_url_rule('/%s' % slug, slug, web_query_handler)
    app.add_url_rule('/%s/json' % slug, slug + "_json", json_query_handler_get, methods=['GET', 'POST'])
