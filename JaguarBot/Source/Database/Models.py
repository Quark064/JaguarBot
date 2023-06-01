from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from enum import IntEnum
from typing import List

from sqlalchemy import select


class TokenType(IntEnum):
    SESSION = 1
    GAME_WEB = 2
    BULLET = 3


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user_table"
    id: Mapped[int] = mapped_column(primary_key=True)
    discordID: Mapped[int]
    language: Mapped[str] = mapped_column(String(7))
    country: Mapped[str] = mapped_column(String(7))

    tokens: Mapped[List["Token"]] = relationship(backref="user", uselist=True)

    def __repr__(self):
        return f"<User {self.id}>"


class Token(Base):
    __tablename__ = "token_table"
    id: Mapped[int] = mapped_column(primary_key=True)
    userID: Mapped[int] = mapped_column(ForeignKey("user_table.id"))

    type: Mapped[int]
    value: Mapped[str] = mapped_column(String())
    expiresAt: Mapped[int]

    def __repr__(self):
        return f"<Token {self.id} -> Parent {self.userID}>"


class AppVersion(Base):
    __tablename__ = "app_version_table"
    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(20))
    version: Mapped[str] = mapped_column(String(20))

    def __repr__(self):
        return f"<AppVersion {self.id}: {self.name}>"


class GraphQLQuery(Base):
    __tablename__ = "graph_ql_query_table"
    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(65))
    hash: Mapped[str] = mapped_column(String(32))


def playground(engine):
    with Session(engine) as session:
        stmt = select(User).where(User.discordID == 123456789)
        userObj = session.scalars(stmt).one()

        stmt = select(Token).where(Token.userID == userObj.id).where(Token.type == TokenType.SESSION)
        token = session.scalars(stmt).one()

        print(token)


if __name__ == "__main__":
    engine = create_engine("sqlite:///UserDB.sqlite", echo=True)
    
    playground(engine)
