from datasethoster.main import create_app, register_query

from example import ExampleQuery, ExampleQuery2

register_query(ExampleQuery())
register_query(ExampleQuery2())

# Needs to be after register_query
app = create_app('config')

if __name__ == "__main__":
    # Only for debugging while developing
    app.run(host='0.0.0.0', debug=True, port=80)
