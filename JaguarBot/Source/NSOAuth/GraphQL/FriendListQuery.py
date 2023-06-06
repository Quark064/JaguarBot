from sqlalchemy.orm import Session
from typing import Tuple

from Database.Models import User
from NSOAuth.GraphQL.GQLRequest import GQLRequest


class FriendListQuery(GQLRequest):
    MAX_PLAYERS = 25
    def __init__(self, dbSession: Session, user: User) -> None:
        self.queryName = __class__.__name__
        self.loggerName = __class__.__name__

        super().__init__(dbSession, user)

    def getPlayingFriends(self) -> Tuple[int, list]:
        """ Returns the number and first MAX_PLAYERS players currently in game. """
        
        friendList = self.gqlResult['data']['friends']['nodes']
        
        onlineFriends = []
        for friend in friendList:
            friendStatus = friend['onlineState']
            if friendStatus != 'ONLINE' and friendStatus != 'OFFLINE':
                onlineFriends.append(friend)
            else:
                break
        
        return (len(onlineFriends), onlineFriends[0:self.MAX_PLAYERS])
