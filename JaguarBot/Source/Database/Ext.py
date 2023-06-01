from time import time
from sqlalchemy import select
from sqlalchemy.orm import Session
from Database.Models import User, Token, GraphQLQuery, TokenType


def getOrCreate(session, model, **kwargs):
    """ Find a given item in the database or create it. """
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        return instance


class FindAbstractor:
    """ Handles common queries. """
    
    def __init__(self, session: Session) -> None:
        self.dbSession = session

    def getToken(self, user: User, tokenType: TokenType) -> Token:
        """ Given a User, find the corresponding token. """
        stmt = select(Token).where(Token.userID == user.id).where(Token.type == tokenType)
        return self.dbSession.scalars(stmt).one()
    
    def getUserFromDID(self, discordID: int) -> User|None:
        """ Given a Discord ID, returns a User. """
        stmt = select(User).where(User.discordID == discordID)
        try:
            return self.dbSession.scalars(stmt).one()
        except Exception:
            return None
    
    def getHashFromName(self, name: str) -> str:
        """ Return the GraphQL Hash from a given Name. """
        stmt = select(GraphQLQuery).where(GraphQLQuery.name == name)
        return self.dbSession.scalars(stmt).one().hash
    
    @staticmethod
    def isTokenExpired(token: Token) -> bool:
        """ Returns a bool if the token is expired or not. """
        return token.expiresAt <= int(time())
