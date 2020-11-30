from datasethoster.main import create_app, register_query

from example import ExampleQuery

app = create_app('config')

register_query(ExampleQuery())

if __name__ == "__main__":
    # Only for debugging while developing
    app.run(host='0.0.0.0', debug=True, port=80)
