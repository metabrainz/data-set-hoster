# MetaBrainz Dataset Hoster

Load/calculate some data, fill out a simple python object, host the results!

As part of our music recommendation engine efforts at MetaBrainz, we're creating a ton of
data sets that are in various states of being useful. In order to be able to evaluate
this data and to start using it in our recommendation tools we needed a quick
way to turn data into a hosted API, so this project was born.

Example
-------

Install the hoster, ideally in a virtual env:

```pip install -e git+ssh://git@github.com/metabrainz/data-set-hoster.git#egg=datasethoster```

Then run this program and go to http://localhost:8000 !

```python
from datasethoster import Query
from datasethoster.main import app, register_query

class ExampleQuery(Query):

    def names(self):
        return ("example", "Useless arithmetic table example")

    def introduction(self):
        return """This is the introduction, which could provide more useful info that this introduction does."""

    def inputs(self):
        return ['number', 'num_lines']

    def outputs(self):
        return ['number', 'multiplied']

    def fetch(self, args, offset=-1, limit=-1):
        data = []
        for arg in args:
            for i in range(int(arg['num_lines'])):
                data.append({ 'number': str(i),
                              'multiplied': str(i * int(arg['number']))
                            })

        return data

register_query(ExampleQuery())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
```

Example
-------

The resulting web page should look something like this:

![Demo web page](/misc/web-page.png)

There is a fully functioning example in the example directory.

Example using JSON
------------------

This project also provides two other endpoints other than the web endpoint:

### GET JSON endpoint

The example above can be fetched using this URL:

```http://localhost:8000/example/json?number=1&num_lines=2```

and the JSON returned will be:

```
[

    {
        "multiplied": "0",
        "number": "0"
    },
    {
        "multiplied": "1",
        "number": "1"
    }

]
```

However, we do not recommend using this endpoint for more than testing,
since the arguments for the GET call can make the URL quite long, which can
give problems with proxies that don't support long enough URLs.

It is best to use the POST JSON endpoint.


### POST JSON endpoint

The example above can be fetched by posting the following JSON

```
[
    {
        "num_lines": "2",
        "number": "1"
    }
]
```

to this URL:

```http://localhost:8000/example/json```

and the JSON returned will be:

```
[

    {
        "multiplied": "0",
        "number": "0"
    },
    {
        "multiplied": "1",
        "number": "1"
    }

]
```

#### Pagination

The JSON POST endpoint (and only it) support pagination. You can add the ```count``` 
and ```offset``` parameters to the URL to control the number and offset
of items returned:

```http://localhost:8000/example/json?count=3&offset=2```


Hosting your own data sets
--------------------------

To host your own data, install the libary as shown above. Then create an object
derived from the Query object and override the following functions:

* names: Return a tuple of the slug (short name) and descrption of this data set. 
         The name should be a simple identifier that provides the dataset a unique 
         location. We recommend using nothing but alphanumeric characters and -.
         The description should give short a human readable description of what your
         data set does.
* introduction: Return a longer description of what the data set is and why your
                user might want to use it.
* inputs: Return a list of required input names. These should be identifiers as well
          with no spaces. If an input is enclosed in [] it denotes that
          a list is required as input to this endpoint. Otherwise the input
          will be a simple value.
* outputs: Return a list of outputs from this functions. These too should be
           identifier names with no spaces and if they are enclosed in []
           it also denotes a list.
* fetch: This is the function where the work is carried out. Given the
         passed in parameters, the function should carry out more error checking
         on the arguments and then fetch the data needed. This function should
         return a list of dicts with keys named exactly after each of the
         outputs. For the POST method endpoint the arguments count and
         offset may be provided -- for the web view and GET JSON views, offset
         and count are not handled.

Once a query object has been defined, it needs to be registered by calling
register_query, passing an instance of the object. Finally you'll need to 
run the app -- the example code shows how to run the app in the development mode.
Please note: Do not use this mode for production -- instead use a proper UWSGI 
container.

If you use Docker, there is a Dockerfile provided in the example directory that
will host this project correctly. See below for more details.


Hosting in Docker with nginx/uwsgi/flask
----------------------------------------

Use the Dockerfile in examples as a template and follow the instructions on how to adapt
the template for your own use. Then build and start the container:

```
docker build -t metabrainz/datasethoster .
docker run -d -p 80:80 metabrainz/datasethoster
```

If you need to connect to another container, you should probably connect the new container 
to the existing network. To connect to an instance of musicbrainz-docker, using an all around more useful 
invocation for testing is:

```
docker run -it --rm --name datasethoster-test --network musicbrainzdocker_default -p 4200:80 metabrainz/datasethoster
```
