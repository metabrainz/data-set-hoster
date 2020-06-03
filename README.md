# data-set-hoster

Load/calculate some data, fill out a simple python object, host the results!

Example
-------

Install the hoster, ideally in a virtual env:

```pip install -e git+ssh://git@github.com/mayhem/data-set-hoster.git#egg=datasethoster```

Then run this program and go to http://localhost:8000 !

```python
from datasethoster import Query
from datasethoster.app import app, register_query

class ExampleQuery(Query):

    def names(self):
        return ("example", "Useless arithmetic table example")

    def inputs(self):
        return ['number', 'num_lines']

    def outputs(self):
        return ['number', 'multiplied']

    def fetch(self, args, offset=-1, limit=-1):
        data = []
        for i in range(1, int(args['num_lines']) + 1):
            data.append({ 'number': str(i), 'multiplied': str(i * int(args['number']))})

        return data

register_query(ExampleQuery())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
```

The base Query class is in datasethoster/__init__.py -- take a look at it to see
what options there are and how to override them.

The resulting web page should look something like this:

![Demo web page](/misc/web-page.png)


Hosting in Docker with nginx/uwsgi/flask:
-----------------------------------------

Use the Dockerfile in examples as a template and follow the instructions on how to adapt
the template for your own use. Then build and start the container:

```
docker build -t mayhem/datasethoster .
docker run -d -p 80:80 mayhem/datasethoster
```

If you need to connect to another container, you should probably connect the new container 
to the existing network. To connect to an instance of musicbrainz-docker, using an all around more useful 
invocation for testing is:

```
docker run -it --rm --name datasethoster-test --network musicbrainzdocker_default -p 4200:80 mayhem/datasethoster
```
