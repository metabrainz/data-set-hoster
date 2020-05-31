from flask import Flask, render_template, request
from werkzeug.exceptions import NotFound

registered_queries = {}

STATIC_PATH = "/static"
STATIC_FOLDER = "../static"
TEMPLATE_FOLDER = "../template"

app = Flask(__name__,
            static_url_path = STATIC_PATH,
            static_folder = STATIC_FOLDER,
            template_folder = TEMPLATE_FOLDER)


@app.route('/')
def index():

    return render_template("index.html", queries=registered_queries)


def query_handler():
    slug = request.path[1:]
    try:
        query = registered_queries[slug]
    except KeyError:
        raise NotFound

    slug, desc = query.names()
    inputs = query.inputs()
    columns = query.outputs()
    args = {}
    try:
        for input in inputs:
            args[input] = request.args[input]
        data = query.fetch(args)
    except KeyError:
        data = None

    return render_template("query.html",
                           data=data,
                           inputs=inputs,
                           columns=columns,
                           args=args,
                           desc=desc,
                           slug=slug)


def register_query(query):

    slug, name = query.names()
    registered_queries[slug] = query
    app.add_url_rule('/%s' % slug, slug, query_handler)
