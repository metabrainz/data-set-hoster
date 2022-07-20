from datasethoster.main import create_app, register_query

from example import ExampleQuery

register_query(ExampleQuery())

# Needs to be after register_query
app = create_app('config')

if __name__ == "__main__":
    # Only for debugging while developing
    app.run(host='0.0.0.0', debug=True, port=80)
