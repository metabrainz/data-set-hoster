import traceback

from flask import Flask, render_template, request, jsonify
from werkzeug.exceptions import NotFound, InternalServerError



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

    return render_template("query.html",
                           error=error,
                           data=data,
                           inputs=inputs,
                           columns=columns,
                           introduction=introduction,
                           args=args,
                           desc=desc,
                           slug=slug)


def json_query_handler():
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
            raise NotFound("Required argument %s missing." % input)
        if not args[input]:
            raise NotFound("Required argument %s cannot be blank." % input)

        # Is the query expecting a list? Check the name of the argument
        # and see if we need to parse the comma seperated arguments into a list
        if input[0] == '[' and input[-1] == ']':
            args[input] = args[input].split(",")

    try:
        data = query.fetch(args)
    except Exception as err:
        print(err)
        return jsonify({}), 500
        
    return jsonify(data)


def register_query(query):

    slug, name = query.names()
    registered_queries[slug] = query
    app.add_url_rule('/%s' % slug, slug, web_query_handler)
    app.add_url_rule('/%s/json' % slug, slug + "_json", json_query_handler)
