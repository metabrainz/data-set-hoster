import os
import traceback
from collections import defaultdict
from datetime import datetime
from enum import Enum
from urllib.parse import urlencode

import sentry_sdk
from flask import Blueprint, Flask, render_template, request, jsonify, redirect, Response
from pydantic import BaseModel
from pydantic.fields import ModelField, SHAPE_NAME_LOOKUP
from sentry_sdk.integrations.flask import FlaskIntegration
from werkzeug.datastructures import MultiDict
from werkzeug.exceptions import BadRequest, MethodNotAllowed

from datasethoster import RequestSource, QueryOutputLine
from datasethoster.decorators import crossdomain
from datasethoster.exceptions import RedirectError


class QueryOutputWrapperModel(BaseModel):
    __root__: list[BaseModel]


DEFAULT_QUERY_RESULT_SIZE = 100
TEMPLATE_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), "template")


registered_queries = {}


dataset_bp = Blueprint('dataset_hoster', __name__, template_folder=TEMPLATE_FOLDER)


def create_app(config_file=None):
    """Create a flask app and optionally load a config file and initialise sentry"""
    app = Flask(__name__, template_folder=TEMPLATE_FOLDER)
    app.jinja_env.tests["datetime_field"] = lambda f: f.type_ == datetime
    app.jinja_env.tests["select_field"] = lambda f: issubclass(f.type_, Enum)
    app.jinja_env.filters["zip"] = zip
    app.register_blueprint(dataset_bp)
    if config_file:
        app.config.from_object(config_file)
    init_sentry(app)
    return app


def init_sentry(app, dsn_config='SENTRY_DSN'):
    """Register sentry on the given app"""
    if dsn_config in app.config and app.config[dsn_config]:
        sentry_sdk.init(
            dsn=app.config[dsn_config],
            integrations=[FlaskIntegration()]
        )

    return app


def register_query(query):
    """
        Applications that use this library must call this function for each query it wishes to host,
        providing a completed Query object that gives all the relevant information about the query.
    """

    query.setup()
    slug, name = query.names()
    registered_queries[slug] = query
    dataset_bp.add_url_rule('/%s' % slug, slug, web_query_handler)
    dataset_bp.add_url_rule('/%s/json' % slug, slug + "_json", json_query_handler, methods=['GET', 'POST', 'OPTIONS'])


@dataset_bp.route('/')
def index():
    """ The home page that shows all of the available queries."""
    return render_template("index.html", queries=registered_queries)


@dataset_bp.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error="Query not found."), 404


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


def fetch_matching_queries(columns: list[str]):
    """ Retrieve queries one of whose input names matches the given column name """
    columns = set(columns)
    matches = []
    for query in registered_queries.values():
        input_model = query.inputs()
        inputs = set(input_model.__fields__.keys())
        matching_columns = columns.intersection(inputs)
        if matching_columns:
            matches.append((query, matching_columns))
    return matches


def get_links_for_output(columns, data):
    """ Generate links to launch other queries for each output item in the data """
    matches = fetch_matching_queries(columns)
    urls = []
    for row in data:
        row_urls = defaultdict(list)
        for (query, columns) in matches:
            slug, name = query.names()
            params = {column: row[column] for column in columns}
            params["dryrun"] = True
            url = f"{slug}?{urlencode(params)}"
            for column in columns:
                row_urls[column].append((name, url))
        urls.append(row_urls)
    return urls


def convert_result_group_to_output(groups: list[tuple[list[str], list[BaseModel]]]):
    """ Convert the result columns and data into an output group by adding similar urls if any """
    outputs = []
    for columns, values in groups:
        output = {
            "columns": columns,
            "data": [x.dict() for x in values],
            "no_table": isinstance(values[0], QueryOutputLine)
        }
        if not output["no_table"]:
            output["links"] = get_links_for_output(output["columns"], output["data"])
        outputs.append(output)
    return outputs


def group_results(results):
    """ Create groups, consecutive outputs till their column list doesn't change, from results """
    if not results:
        return []

    groups = []
    last_result, last_keys, last_group = results[0], results[0].__fields__.keys(), []
    for result in results:
        current_keys = result.__fields__.keys()
        if current_keys != last_keys:
            groups.append((last_keys, last_group))
            last_keys, last_group = current_keys, []
        last_result = result
        last_group.append(result)

    if last_result and last_keys and last_group:
        groups.append((last_keys, last_group))

    return groups


def convert_args_to_input(input_model: BaseModel, arguments: MultiDict):
    """ Convert the request arguments (query parameters) to input for passing to query. """
    params = {}
    for key, values in arguments.lists():
        # user submitted multiple values for query parameter pass all to field in all cases, model will raise
        # a ValidationError in case of mismatch
        if len(values) > 1:
            params[key] = values
        else:
            # user submitted only one value, check if the model expects a list or a single value
            # and coerce it accordingly
            field = input_model.__fields__.get(key)

            # iterable/list expecting shapes are present in SHAPE_NAME_LOOKUP dict in pydantic
            if field is not None and field.shape in SHAPE_NAME_LOOKUP:
                params[key] = values
            else:
                params[key] = values[0]
    return params


def web_query_handler():
    """
        This is the view handler for the web page. It is more complex because of all
        the guff shown on the web page to make it easy to discover these data sets.
    """
    query, error = fetch_query(request.path)
    if error:
        return render_template("error.html", error=error)

    offset = int(request.args.get('offset', "-1"))
    count = int(request.args.get('count', "-1"))
    if offset >= 0 or count >= 0:
        return render_template("error.html", error="offset and count arguments are only supported for the POST method")
    dryrun = request.args.get("dryrun", None)

    slug, desc = query.names()
    introduction = query.introduction()
    input_model = query.inputs()
    json_url = request.url.replace(slug, slug + "/json")

    outputs = []
    json_post = ""
    if request.args and not dryrun:
        try:
            params = convert_args_to_input(input_model, request.args)
            inputs = [input_model(**params)]
            results = query.fetch(inputs, RequestSource.web)
        except RedirectError as red:
            return redirect(red.url)
        except Exception as err:
            error = traceback.format_exc()
            sentry_sdk.capture_exception(err)
            return render_template("error.html", error=error)

        groups = group_results(results)
        outputs = convert_result_group_to_output(groups)

        json_post = QueryOutputWrapperModel(__root__=inputs).json(indent=4)

    return render_template(
        "query.html",
        error=error,
        fields=input_model.__fields__.values(),
        results=outputs,
        introduction=introduction,
        args=request.args,
        desc=desc,
        slug=slug,
        json_url=json_url,
        json_post=json_post,
        additional_data=query.additional_data()
    )


@crossdomain(headers=["Content-Type"])
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

    offset = int(request.args.get('offset', "-1"))
    count = int(request.args.get('count', "-1"))
    if offset >= 0 or count >= 0:
        raise BadRequest("offset and count arguments are only supported for the POST method")

    input_model = query.inputs()

    try:
        params = convert_args_to_input(input_model, request.args)
        inputs = [input_model(**params)]
    except Exception as e:
        raise BadRequest(str(e))

    try:
        data = query.fetch(inputs, RequestSource.json_get)
        result = QueryOutputWrapperModel(__root__=data)
    except Exception as err:
        sentry_sdk.capture_exception(err)
        print(traceback.format_exc())
        return jsonify({}), 500

    return Response(result.json(), mimetype="application/json")


def json_query_handler_post():
    """
        The POST view handler. Sanity check parameters, run the query and return it.
        Simple!
    """
    query, error = fetch_query(request.path)
    if error:
        raise BadRequest(error)

    input_model = query.inputs()

    inputs = []
    try:
        for item in request.json:
            inputs.append(input_model(**item))
    except Exception as e:
        raise BadRequest(str(e))

    offset = int(request.args.get('offset', "0"))
    count = int(request.args.get('count', str(DEFAULT_QUERY_RESULT_SIZE)))

    try:
        data = query.fetch(inputs, RequestSource.json_post, offset=offset, count=count)
        result = QueryOutputWrapperModel(__root__=data)
    except Exception as err:
        sentry_sdk.capture_exception(err)
        print(traceback.format_exc())
        return jsonify({"error": err}), 400

    return Response(result.json(), mimetype="application/json")
