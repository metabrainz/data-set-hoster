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
        return ("", "")

    @abstractmethod
    def introduction(self):
        """ Return a text to be shown on top of the query page that acts as an intro to this query."""
        return ("", "")

    @abstractmethod
    def inputs(self):
        """ return a list of text column names that are required inputs for this query.
            column names that are enclosed in [] indicates that the query expects a list,
            rather than a simple text argument
        """
        return []

    @abstractmethod
    def outputs(self):
        """ return a list of text column names that will be returned by the fetch function """
        return []

    @abstractmethod
    def fetch(self, params, offset=-1, limit=-1):
        """ return a list of rows of columns of data to be shown in the page. """
        return []

