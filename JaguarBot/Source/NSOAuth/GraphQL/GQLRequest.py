from sqlalchemy.orm import Session
from requests import post
from json import loads

from Database.Models import User, TokenType
from Database.Ext import FindAbstractor
from Helpers.Logger import Logger
from NSOAuth.RefreshManager import RefreshManager
from NSOAuth.VersionManager import VersionManager

class GQLRequest:
    """ Interface that defines how GraphQL Requests are made. """

    GRAPHQL_ENDPOINT = "https://api.lp1.av5ja.srv.nintendo.net/api/graphql"

    def __init__(self, dbSession: Session, user: User) -> None:
        # Replaced in Subclass
        self.queryName: str
        self.gqlResult: dict
        self.loggerName: str
        
        # Common
        self.logger = Logger(self.loggerName)
        self.dbSession: Session = dbSession
        self.user: User = user
        self.fAbs = FindAbstractor(self.dbSession)
        self.vManager = VersionManager(self.dbSession)

    async def refreshTokens(self, user: User) -> bool|None:
        """ Attempts to refresh invalid tokens.
            Returns True if the tokens were updated, False if they failed to update,
            and returns None if the tokens were not expired. """
        
        gToken = self.fAbs.getToken(user, TokenType.GAME_WEB)
        bToken = self.fAbs.getToken(user, TokenType.BULLET)

        if self.fAbs.isTokenExpired(gToken):
            return await RefreshManager.refreshGameWeb(self.dbSession, user)
        
        if self.fAbs.isTokenExpired(bToken):
            if not await RefreshManager.refreshBullet(self.dbSession, user):
                return await RefreshManager.refreshGameWeb(self.dbSession, user)
    

    async def sendGQLRequest(self, **kwargs) -> bool:
        """ Sends the GraphQL Request to the server. Returns bool if it was successful."""

        # Refresh known expired tokens
        status = await self.refreshTokens(self.user)
        if status != None:
            if status:
                self.logger.log(f"Refreshed tokens for User {self.user.discordID}")
            else:
                self.logger.warn(f"Failed to refresh tokens for User {self.user.discordID}!")

        gToken = self.fAbs.getToken(self.user, TokenType.GAME_WEB)
        bToken = self.fAbs.getToken(self.user, TokenType.BULLET)
        
        header = {
            'Authorization':    f'Bearer {bToken.value}',
            'Accept-Language':  self.user.language,
            'User-Agent':       "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Mobile Safari/537.36",
            'X-Web-View-Ver':   self.vManager.getAppVersions().s3Version,
            'Content-Type':     'application/json',
            'Accept':           '*/*',
            'Origin':           self.GRAPHQL_ENDPOINT,
            'X-Requested-With': 'com.nintendo.znca',
            'Referer':          f'{self.GRAPHQL_ENDPOINT}?lang={self.user.language}',
            'Accept-Encoding':  'gzip, deflate'
        }

        body = {
            "variables": kwargs,
            "extensions": {
              "persistedQuery": {
                "version": 1,
                "sha256Hash": self.fAbs.getHashFromName(self.queryName)
              }
            }
        }

        cookies = {
        	'_gtoken': gToken.value,
        	'_dnt':    '1'
        }

        try:
            r = post(self.GRAPHQL_ENDPOINT, headers=header, json=body, cookies=cookies)
            
            if r.status_code != 200:
                if not await RefreshManager.refreshGameWeb(self.dbSession, self.user):
                    self.logger.warn(f"Failed to refresh tokens after initial failure for User {self.user.discordID}")
                    return False
                else:
                    self.logger.log(f"Refreshed tokens after initial failure for User {self.user.discordID}")
                
                header['Authorization'] = f'Bearer {self.fAbs.getToken(self.user, TokenType.BULLET).value}'
                cookies['_gtoken'] = self.fAbs.getToken(self.user, TokenType.GAME_WEB).value
                
                r = post(self.GRAPHQL_ENDPOINT, headers=header, json=body, cookies=cookies)
                
                if r.status_code != 200:
                    self.logger.warn(f"Second request failed after successful token refresh for User {self.user.discordID}!")
                    return False

            self.gqlResult = loads(r.text)
        except Exception as ex:
            self.logger.warn(f"Get failure with User {self.user.discordID} -> {str(ex)}")
            return False
        
        return True
