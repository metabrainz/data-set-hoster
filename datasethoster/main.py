from collections import defaultdict
import copy
import traceback
import json

from flask import Flask, render_template, request, jsonify
from werkzeug.exceptions import NotFound, BadRequest, InternalServerError, MethodNotAllowed


registered_queries = {}

TEMPLATE_FOLDER = "template"

app = Flask(__name__,
            template_folder = TEMPLATE_FOLDER)


@app.route('/')
def index():
    return render_template("index.html", queries=registered_queries)


def fetch_query(url):
    parts = url[1:].split("/")
    slug = parts[0]
    try:
        query = registered_queries[slug]
    except KeyError:
        raise NotFound

    return query


def convert_http_args_to_json(inputs, req_args):

    args = {}
    num_args = 0
    list_len = -1
    for arg in req_args:
        args[arg] = req_args[arg].split(",")
        num_args = len(args[arg])
        list_len = max(list_len, len(args[arg]))

    singletons = {}
    for arg in args:
        if len(args[arg]) > 1 and len(args[arg]) != list_len:
            return [], "Lists passed as parameters must all be the same length."

        if len(args[arg]) == 1:
            singletons[arg] = args[arg][0]

    arg_list = []
    for i in range(list_len):
        row = copy.deepcopy(singletons)
        for input in inputs:
            if input not in singletons:
                row[input] = args[input][i]
        arg_list.append(row)

    return arg_list, ""


def error_check_arguments(inputs, req_json):

    for i, row in enumerate(req_json):
        for input in inputs:
            if not input in row:
                raise BadRequest("Required argument '%s' missing in row %d." % (input, i))
            if not row[input]:
                raise BadRequest("Required argument '%s' cannot be blank." % (input, i))

def web_query_handler():

    query = fetch_query(request.path)
    slug, desc = query.names()
    introduction = query.introduction()
    inputs = query.inputs()
    outputs = query.outputs()

    data = []
    json_post = ""
    arg_list, error = convert_http_args_to_json(inputs, request.args)
    if not error:
        error_check_arguments(inputs, arg_list)
        if arg_list:
            json_post = json.dumps(arg_list, indent=4, sort_keys=True)
        print("json_post '%s'" % json_post)

        try:
            data = query.fetch(arg_list) if arg_list else []
        except Exception as err:
            error = traceback.format_exc()
            print(error)

        for i, arg in enumerate(data):
            for output in outputs:
                if output[0] == '[' and output[-1] == ']':
                    try:
                        arg[output] = ",".join(arg[output])
                    except KeyError:
                        pass

    json_url = request.url.replace(slug, slug + "/json")
    return render_template("query.html",
                           error=error,
                           data=data,
                           count=len(data) if data else -1,
                           inputs=inputs,
                           columns=outputs,
                           introduction=introduction,
                           args=request.args,
                           desc=desc,
                           slug=slug,
                           json_url=json_url,
                           json_post=json_post)


def json_query_handler():
    if request.method == 'GET':
        return json_query_handler_get()

    if request.method == 'POST':
        return json_query_handler_post()

    raise MethodNotAllowed


def json_query_handler_get():

    query = fetch_query(request.path)
    slug, desc = query.names()
    inputs = query.inputs()
    columns = query.outputs()

    arg_list, error = convert_http_args_to_json(inputs, request.args)
    if error:
        raise BadRequest(error)

    error_check_arguments(inputs, arg_list)

    try:
        data = query.fetch(arg_list) if arg_list else []
    except Exception as err:
        print(traceback.format_exc())
        return jsonify({}), 500

    return jsonify(data)


def json_query_handler_post():

    if not isinstance(request.json, list):
        raise BadRequest("POST data must be a JSON list of hashes.")

    query = fetch_query(request.path)
    inputs = query.inputs()
    outputs = query.outputs()

    error_check_arguments(inputs, request.json)

    try:
        data = query.fetch(request.json) if request.json else []
    except Exception as err:
        print(traceback.format_exc())
        return jsonify({}), 500

    return jsonify(data)

def register_query(query):

    slug, name = query.names()
    registered_queries[slug] = query
    app.add_url_rule('/%s' % slug, slug, web_query_handler)
    app.add_url_rule('/%s/json' % slug, slug + "_json", json_query_handler, methods=['GET', 'POST'])
