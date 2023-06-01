from sqlalchemy.orm import Session

from Database.Models import User
from NSOAuth.TokenManager import TokenManager
from NSOAuth.VersionManager import VersionManager, VersionInfo

class GQLRequest:
    """ Interface that defines how GraphQL Requests are made. """

    def __init__(self, dbSession: Session, user: User) -> None:
        self.queryName: str
        
        self.dbSession: Session = dbSession
        self.user: User = user