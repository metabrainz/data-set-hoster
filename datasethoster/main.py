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

def register_query(query):
    """
        Applications that use this library must call this function for each query it wishes to host,
        providing a completed Query object that gives all the relevant information about the query.
    """

    slug, name = query.names()
    registered_queries[slug] = query
    app.add_url_rule('/%s' % slug, slug, web_query_handler)
    app.add_url_rule('/%s/json' % slug, slug + "_json", json_query_handler, methods=['GET', 'POST'])


@app.route('/')
def index():
    """ The home page that shows all of the available queries."""
    return render_template("index.html", queries=registered_queries)


def fetch_query(url):
    """ 
        Helper function to lookup and return a query object. Return None and error string
        if not query is found. Otherwise query and an empty error string.
    """
    parts = url[1:].split("/")
    slug = parts[0]
    try:
        query = registered_queries[slug]
    except KeyError:
        return None, "Requested query '%s' not hosted on this site." % slug

    return query, ""


def convert_http_args_to_json(inputs, req_args):
    """
        THis function converts a series of HTTP arguments into a sane JSON (dict)
        that mimicks the data that is passed to the POST function. Also does
        some error checking on the data. Returns a complete dict or parameters 
        and a blank string or None and an error string.
    """

    args = {}
    num_args = 0
    list_len = -1
    for arg in req_args:
        args[arg] = req_args[arg].split(",")
        num_args = len(args[arg])
        list_len = max(list_len, len(args[arg]))

    singletons = {}
    for arg in args:
        if arg.startswith("[") and len(args[arg]) != list_len:
            return [], "Lists passed as parameters must all be the same length."

        if len(args[arg]) == 1:
            singletons[arg] = args[arg][0]

    arg_list = []
    try:
        for i in range(list_len):
            row = copy.deepcopy(singletons)
            for input in inputs:
                if input not in args:
                    return [], "Missing parameter '%s'." % input
                if input not in singletons:
                    row[input] = args[input][i]
            arg_list.append(row)
    except KeyError as err:
        return [], "KeyError: " + str(err)

    return arg_list, ""


def error_check_arguments(inputs, req_json):
    """
        Given the JSON (dict) version of the parameters, ensure that they are sane.
        Parameters must all be available for each row and parameters cannot be blank.
        If there are parameters that are lists, make sure all lists contain
        the same number of elements. Returns error string if error, otherwise empty string
    """

    if not req_json:
        return "No parameters supplied. Required: %s" % (",".join(inputs))

    for i, row in enumerate(req_json):
        for input in inputs:
            if not input in row:
                return "Required parameter '%s' missing in row %d." % (input, i)
            if not row[input]:
                return "Required parameter '%s' cannot be blank." % (input, i)

    # Examine one row to ensure that all the parameters are there.
    for req in req_json[0]:
        if req not in inputs:
            return "Too many parameters passed. Extra: '%s'" % req

    return ""


def web_query_handler():
    """
        This is the view handler for the web page. It is more complex because of all
        the guff shown on the web page to make it easy to discover these data sets.
    """

    query, error = fetch_query(request.path)
    if not error:
        slug, desc = query.names()
        introduction = query.introduction()
        inputs = query.inputs()
        outputs = query.outputs()

        data = []
        json_post = ""
        arg_list, error = convert_http_args_to_json(inputs, request.args)
        if arg_list and not error:
            error = error_check_arguments(inputs, arg_list)
            if not error:
                if arg_list:
                    json_post = json.dumps(arg_list, indent=4, sort_keys=True)

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
    """
        Disambiguate between GET and POST requests and direct accordingly.
    """

    if request.method == 'GET':
        return json_query_handler_get()

    if request.method == 'POST':
        return json_query_handler_post()

    raise MethodNotAllowed


def json_query_handler_get():
    """
        Handle a GET request. GET request should only ever be used if you're
        certain that you're not going to request a result with too many
        query parameters. If you need more than a handful of parameters,
        use the POST method instead.
    """

    query, error = fetch_query(request.path)
    if error:
        raise BadRequest(error)

    slug, desc = query.names()
    inputs = query.inputs()
    columns = query.outputs()

    arg_list, error = convert_http_args_to_json(inputs, request.args)
    if error:
        raise BadRequest(error)

    error = error_check_arguments(inputs, arg_list)
    if error:
        raise BadRequest(error)

    try:
        data = query.fetch(arg_list) if arg_list else []
    except Exception as err:
        print(traceback.format_exc())
        return jsonify({}), 500

    return jsonify(data)


def json_query_handler_post():
    """
        The POST view handler. Sanity check parameters, run the query and return it.
        Simple!
    """

    if not isinstance(request.json, list):
        raise BadRequest("POST data must be a JSON list of hashes.")

    query, error = fetch_query(request.path)
    if error:
        raise BadRequest(error)

    inputs = query.inputs()
    outputs = query.outputs()

    error = error_check_arguments(inputs, request.json)
    if error:
        raise BadRequest(error)

    try:
        data = query.fetch(request.json) if request.json else []
    except Exception as err:
        print(traceback.format_exc())
        return jsonify({}), 500

    return jsonify(data)
