class RedirectError(Exception):
    """ Indicates that we should redirect to a new URL instead of show results. """

    def __init__(self, url):
        self.url = url
        super().__init__()

class QueryError(Exception):
    """Raise from a Query's fetch() method to return a user-facing error.

    For web views, the message is displayed on the error page. For JSON API
    views, the response body is {"error": message, "code": status_code}.

    Args:
        message: A human-readable error description shown to the user.
        status_code: The HTTP status code for the response (default 400).
    """

    def __init__(self, message: str = None, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)
