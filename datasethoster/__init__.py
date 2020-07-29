from abc import abstractmethod


class Query():

    def __init__(self):
        """ The constructor, override it if you need to. """
        pass

    @abstractmethod
    def setup(self):
        """ This method is called once the class is ready to be started. Load data/indexes or
            whatever you may need at this point. """
        pass

    @abstractmethod
    def names(self):
        """ Return a short name (slug) and a more descriptive name """
        pass

    @abstractmethod
    def introduction(self):
        """ Return a text to be shown on top of the query page that acts as an intro to this query."""
        pass

    @abstractmethod
    def inputs(self):
        """ return a list of text column names that are required inputs for this query.
            column names that are enclosed in [] indicates that the query expects a list,
            rather than a simple text argument
        """
        pass

    @abstractmethod
    def outputs(self):
        """ return a list of text column names that will be returned by the fetch function """
        pass

    @abstractmethod
    def fetch(self, params, offset=-1, limit=-1):
        """
           Given the passed in parameters, the function should carry out more error checking
           on the arguments and then fetch the data needed. This function should
           return a list of dicts with keys named exactly after each of the
           outputs. This function should use the Werkzeug exceptions like NotFound, BadRequest
           if anything goes wrong in the process of fetching the data. For the web interface
           BadRequest, InternalServerError, ImATeapot, ServiceUnavailable, NotFound are caught
           and the text is correctly displayed as an error on the web page.
        """
        pass
