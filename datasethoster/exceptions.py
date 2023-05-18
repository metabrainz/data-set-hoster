class RedirectError(Exception):
    """ Indicates that we should redirect to a new URL instead of show results. """

    def __init__(self, url):
        self.url = url
        super().__init__()

class QueryError(Exception):
    """ An error occured during the execution of the query and the error should be shown to the user. """
