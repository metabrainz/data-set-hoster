class RedirectError(Exception):
    """ Indicates that we should redirect to a new URL instead of show results. """

    def __init__(self, url):
        self.url = url
        super().__init__()
