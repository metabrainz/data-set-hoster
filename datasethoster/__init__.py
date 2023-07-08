from abc import abstractmethod
from enum import Enum
from typing import TypeVar, Generic, Type

from pydantic import BaseModel

QueryInT = TypeVar('QueryInT', bound=BaseModel)
QueryOutT = TypeVar('QueryOutT', bound=BaseModel)


class RequestSource(Enum):
    web = "web"
    json_get = "json_get"
    json_post = "json_post"


class QueryOutputLine(BaseModel):
    line: str


class Query(Generic[QueryInT, QueryOutT]):

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
    def inputs(self) -> Type[QueryInT]:
        """ return a list of text column names that are required inputs for this query.
            column names that are enclosed in [] indicates that the query expects a list,
            rather than a simple text argument
        """
        pass

    @abstractmethod
    def outputs(self) -> Type[QueryOutT]:
        """ return a list of text column names that will be returned by the fetch function.
            return None if the outputs are dynamic and you want those to be inferred.
        """
        pass

    @abstractmethod
    def fetch(self, params: QueryInT, source: RequestSource, offset=-1, limit=-1) -> QueryOutT:
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

    def additional_data(self):
        """ return a dict of data that can provide hints to the dataset hoster.

            Supported keys:
                playlist_name: the name of the playlist, should the user want to save the result data as a playlist.
                playlist_desc: the desc of the playlist, should the user want to save the result data as a playlist.
        """
        return {"name": "Instant Playlist", "desc": "Instant Playlist"}
