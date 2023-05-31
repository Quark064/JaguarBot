import requests

from base64 import urlsafe_b64encode
from hashlib import sha256
from os import urandom
from urllib.parse import urlencode
from re import search
from json import loads, dumps
from enum import Enum, IntEnum, auto
from dataclasses import dataclass
from typing import Self
from NSOAuth.VersionManager import VersionInfo

import Config


# ENUMS --------------------
class Status(Enum):
    OK = auto()
    ERROR = auto()

class TKError(Enum):
    GENERAL = auto()
    INVALID_URL = auto()
    MISSING_KEYS = auto()
    KEY_EXPIRED = auto()
    GET_FAILURE = auto()
    USER_NOT_REGISTERED = 204
    ERROR_INVALID_GAME_WEB_TOKEN = 401
    ERROR_OBSOLETE_VERSION = 403
    INVALID_TOKEN = 9403

class FStep(IntEnum):
    LOGIN_TOKEN = 1
    G_TOKEN = 2


# HELPER DATACLASSES -------
@dataclass
class OperationResult:
    status: Status
    message: str|None
    errorType: TKError|None


# RETURN DATACLASSES -------
class TKResult:
    def __init__(self) -> None:
        self.result: OperationResult
    
    def statusError(self, errorType: TKError|None, msg: str|None = None) -> Self:
        """ Sets the OperationResult to an Error State. """
        self.result = OperationResult(
                    Status.ERROR,
                    msg,
                    errorType
            )
        return self
    
    def statusOK(self, msg: str|None = None) -> Self:
        """ Sets the OperationResult to an OK State. """
        self.result = OperationResult(
                    Status.OK,
                    msg,
                    None
            )
        return self

@dataclass
class AuthURLResult(TKResult):
    state: bytes
    challenge: bytes
    verifier: bytes
    url: str

@dataclass(init=False)
class NinUserResult(TKResult):
    nickname:    str
    language:    str
    country:     str
    birthday:    str
    accountID:   str
    idToken:     str
    accessToken: str

@dataclass(init=False)
class FToken(TKResult):
    f: str
    uuid: str
    timestamp: str

@dataclass(init=False)
class WebAPIResult(TKResult):
    webLoginToken: str
    coralID: str

@dataclass(init=False)
class StringResult(TKResult):
    value: str


# MANAGING CLASS ----------
class TokenManager:
    """ Manages authentication to NSO Services. """

    # Public Methods ----------
    def __init__(self, verInfo: VersionInfo) -> None:
        self.verInfo = verInfo


    async def generateNSOLoginLink(self) -> AuthURLResult:
        """ Generate a login URL for a user to authenticate their account. """

        authState = urlsafe_b64encode(urandom(36))
        
        authVerifier = urlsafe_b64encode(urandom(32))
        authVerifier = authVerifier.replace(b"=", b"")
        
        authCVHash = sha256()
        authCVHash.update(authVerifier)
        
        authChallenge = urlsafe_b64encode(authCVHash.digest())
        authChallenge = authChallenge.replace(b"=", b"")

        body = {
        	'state':                               authState,
        	'redirect_uri':                        'npf71b963c1b7b6d119://auth',
        	'client_id':                           '71b963c1b7b6d119',
        	'scope':                               'openid user user.birthday user.mii user.screenName',
        	'response_type':                       'session_token_code',
        	'session_token_code_challenge':        authChallenge,
        	'session_token_code_challenge_method': 'S256',
        	'theme':                               'login_form'
        }

        authResult = AuthURLResult(
            state=authState,
            challenge=authChallenge,
            verifier=authVerifier,
            url=f"https://accounts.nintendo.com/connect/1.0.0/authorize?{urlencode(body)}"
        )

        return authResult.statusOK()


    async def generateSessionToken(self, givenURL: str, authInfo: AuthURLResult) -> StringResult:
        """ Create a Session Token given the Session Code. """
        
        rawCode = search('de=(.*)&', givenURL)
        if rawCode:
            sessionCode = rawCode.group(1)
        else:
            return StringResult().statusError(TKError.INVALID_URL, f"The provided URL was not valid.")

        appHead = {
        	'User-Agent':      f'OnlineLounge/{self.verInfo.nsoVersion} NASDKAPI Android',
        	'Accept-Language': 'en-US',
        	'Accept':          'application/json',
        	'Content-Type':    'application/x-www-form-urlencoded',
        	'Content-Length':  '540',
        	'Host':            'accounts.nintendo.com',
        	'Connection':      'Keep-Alive',
        	'Accept-Encoding': 'gzip'
        }

        body = {
        	'client_id':                   '71b963c1b7b6d119',
        	'session_token_code':          sessionCode,
        	'session_token_code_verifier': authInfo.verifier
        }

        url = 'https://accounts.nintendo.com/connect/1.0.0/api/session_token'

        try:
            with requests.Session() as requestSession:
                request = requestSession.post(url, headers=appHead, data=body)
                sessionToken = loads(request.text)["session_token"]
        except Exception:
            return StringResult().statusError(TKError.GET_FAILURE, f"Unable to get Session Token.")
        
        
        returnVal = StringResult()
        returnVal.value = sessionToken

        return returnVal.statusOK()
    

    async def generateGToken(self, sessionToken: str) -> StringResult:
        """ Generate a GToken given a valid session token. """

        ninUserInfo = self.__getNintendoUserInfo(sessionToken)

        res = ninUserInfo.result
        if res.status != Status.OK:
            return StringResult().statusError(res.errorType, res.message)
        
        webAPI = self.__getWebAPIToken(ninUserInfo)

        res = webAPI.result
        if res.status != Status.OK:
            return StringResult().statusError(res.errorType, res.message)
        
        return self.__getGToken(ninUserInfo, webAPI)


    async def generateBulletToken(self, sessionToken: str, gToken: str) -> StringResult:
        """ Using the VersionInfo, the Session Token, and a GToken, get a Bullet Token. """
        
        ninUserInfo = self.__getNintendoUserInfo(sessionToken)

        res = ninUserInfo.result
        if res.status != Status.OK:
            return StringResult().statusError(res.errorType, res.message)
        
        return self.__getBulletToken(ninUserInfo, gToken)
        


    # Private Helper Methods ----
    @staticmethod
    def __getNintendoUserInfo(sessionToken: str) -> NinUserResult:
        """ Request a user's information with their Session Token. """

        ninUser = NinUserResult()

        appHead = {
        	'Host':            'accounts.nintendo.com',
        	'Accept-Encoding': 'gzip',
        	'Content-Type':    'application/json',
        	'Content-Length':  '436',
        	'Accept':          'application/json',
        	'Connection':      'Keep-Alive',
        	'User-Agent':      'Dalvik/2.1.0 (Linux; U; Android 7.1.2)'
        }

        body = {
        	'client_id':     '71b963c1b7b6d119',
        	'session_token': sessionToken,
        	'grant_type':    'urn:ietf:params:oauth:grant-type:jwt-bearer-session-token'
        }

        try:
            url = "https://accounts.nintendo.com/connect/1.0.0/api/token"
            r = requests.post(url, headers=appHead, json=body)

            match(r.status_code):
                case 400:
                    return NinUserResult().statusError(TKError.GET_FAILURE, "Session Token was incorrect.")
                case 401:
                    return NinUserResult().statusError(TKError.INVALID_TOKEN, "The Session Token was rejected.")

            res = loads(r.text)
            ninUser.idToken     = res["id_token"]
            ninUser.accessToken = res["access_token"]
        except Exception:
            return NinUserResult().statusError(TKError.GET_FAILURE, "Unable to get ID/Access Token.")
        
        appHead = {
        	'User-Agent':      'NASDKAPI; Android',
        	'Content-Type':    'application/json',
        	'Accept':          'application/json',
        	'Authorization':   f'Bearer {ninUser.accessToken}',
        	'Host':            'api.accounts.nintendo.com',
        	'Connection':      'Keep-Alive',
        	'Accept-Encoding': 'gzip'
        }

        try:
            url = "https://api.accounts.nintendo.com/2.0.0/users/me"
            r = requests.get(url, headers=appHead)
            userInfo = loads(r.text)
            
            ninUser.nickname  = userInfo["nickname"]
            ninUser.language  = userInfo["language"]
            ninUser.country   = userInfo["country"]
            ninUser.birthday  = userInfo["birthday"]
            ninUser.accountID = userInfo['id']
        except Exception:
            return NinUserResult().statusError(TKError.GET_FAILURE, "Unable to get Nintendo User Info.")
        
        return ninUser.statusOK()


    def __generateFToken(self, fStep: int, idToken: str, accountID: str|None = None, coralID: str|None = None) -> FToken:
        """ Reach out to the fAPI and request an 'f' token.
        
            All hash methods suggest supplying the Nintendo Account ID.
            
            The Coral ID should only be supplied when using FStep.G_TOKEN. """

        apiHead = {
            'X-znca-Platform': 'Android',
            'X-znca-Version': self.verInfo.nsoVersion,
        	'User-Agent':   f'{Config.SERVER_NAME}/{Config.SERVER_VERSION}',
        	'Content-Type': 'application/json; charset=utf-8',
        }
        apiBody = {
        	'token':       idToken,
        	'hash_method': int(fStep)
        }

        if accountID:
            apiBody['na_id'] = accountID
        if coralID and fStep == FStep.G_TOKEN:
            apiBody['coral_user_id'] = coralID

        try:
            apiResponse = requests.post(Config.F_ENDPOINT, data=dumps(apiBody), headers=apiHead)
            res = loads(apiResponse.text)

            f         = res["f"]
            uuid      = res["request_id"]
            timestamp = res["timestamp"]
        except Exception:
            return FToken().statusError(TKError.GET_FAILURE, f"Unable to get type {fStep} `f` token from the Community API.")
        
        fToken = FToken()
        fToken.f = f
        fToken.uuid = uuid
        fToken.timestamp = timestamp

        return fToken.statusOK()


    def __getWebAPIToken(self, userInfo: NinUserResult) -> WebAPIResult:
        """ Using a user's information, generate a WebAccess token. """

        resF = self.__generateFToken(FStep.LOGIN_TOKEN, userInfo.idToken, userInfo.accountID)
        
        if resF.result.status != Status.OK:
            return WebAPIResult().statusError(resF.result.errorType, resF.result.message)

        appHead = {
        	'X-Platform':       'Android',
        	'X-ProductVersion': self.verInfo.nsoVersion,
        	'Content-Type':     'application/json; charset=utf-8',
        	'Content-Length':   str(990 + len(resF.f)),
        	'Connection':       'Keep-Alive',
        	'Accept-Encoding':  'gzip',
        	'User-Agent':       f'com.nintendo.znca/{self.verInfo.nsoVersion}(Android/7.1.2)',
        }
                
        body = {
            "parameter": {
                'f':          resF.f,
                'language':   userInfo.language,
                'naBirthday': userInfo.birthday,
                'naCountry':  userInfo.country,
                'naIdToken':  userInfo.idToken,
                'requestId':  resF.uuid,
                'timestamp':  resF.timestamp
		    }
        }

        try:
            url = "https://api-lp1.znc.srv.nintendo.net/v3/Account/Login"
            r = requests.post(url, headers=appHead, json=body)
            result = loads(r.text)

            webLoginToken = result["result"]["webApiServerCredential"]["accessToken"]
            coralToken    = str(result["result"]["user"]["id"])
        except Exception:
            return WebAPIResult().statusError(TKError.GET_FAILURE, "Unable to get WebAPI/Coral Token.")
        
        ret = WebAPIResult()
        ret.webLoginToken = webLoginToken
        ret.coralID = coralToken
        
        return ret.statusOK()


    def __getGToken(self, userInfo: NinUserResult, webAPI: WebAPIResult) -> StringResult:
        """ Using a WebAPI token, generate a WebService token."""

        resF = self.__generateFToken(FStep.G_TOKEN, webAPI.webLoginToken, userInfo.accountID, webAPI.coralID)

        appHead = {
        	'X-Platform':       'Android',
        	'X-ProductVersion': self.verInfo.nsoVersion,
        	'Authorization':    f'Bearer {webAPI.webLoginToken}',
        	'Content-Type':     'application/json; charset=utf-8',
        	'Content-Length':   '391',
        	'Accept-Encoding':  'gzip',
        	'User-Agent':       f'com.nintendo.znca/{self.verInfo.nsoVersion}(Android/7.1.2)'
        }

        body = {
            "parameter": {
        	    'f':                 resF.f,
        	    'id':                4834290508791808,
        	    'registrationToken': webAPI.webLoginToken,
        	    'requestId':         resF.uuid,
        	    'timestamp':         resF.timestamp
            }
        }

        try:
            url = "https://api-lp1.znc.srv.nintendo.net/v2/Game/GetWebServiceToken"
            result = requests.post(url, headers=appHead, json=body)
            gToken = loads(result.text)["result"]["accessToken"]
        except Exception:
            return StringResult().statusError(TKError.GET_FAILURE, "Unable to get GToken.")

        stringRes = StringResult()
        stringRes.value = gToken
        
        return stringRes.statusOK()


    def __getBulletToken(self, userInfo: NinUserResult, gToken: str) -> StringResult:
        """ Using a WebService token, request a Bullet token. """

        appHead = {
        	'Content-Length':   '0',
        	'Content-Type':     'application/json',
        	'Accept-Language':  userInfo.language,
        	'User-Agent':       'Mozilla/5.0 (Linux; Android 11; Pixel 5) ' \
						        'AppleWebKit/537.36 (KHTML, like Gecko) ' \
						        'Chrome/94.0.4606.61 Mobile Safari/537.36',
        	'X-Web-View-Ver':   self.verInfo.s3Version,
        	'X-NACOUNTRY':      userInfo.country,
        	'Accept':           '*/*',
        	'Origin':           'https://api.lp1.av5ja.srv.nintendo.net',
        	'X-Requested-With': 'com.nintendo.znca'
        }
        appCookies = {
        	'_gtoken': gToken,  # X-GameWebToken
        	'_dnt':    '1'      # Do Not Track
        }

        try:
            url = 'https://api.lp1.av5ja.srv.nintendo.net/api/bullet_tokens'
            r = requests.post(url, headers=appHead, cookies=appCookies)

            match(r.status_code):
                case 204:
                    return StringResult().statusError(TKError.USER_NOT_REGISTERED, "You must play at least one game online to use this application.")
                case 401:
                    return StringResult().statusError(TKError.INVALID_TOKEN, "The GameWebToken has expired.")
                case 403:
                    return StringResult().statusError(TKError.ERROR_OBSOLETE_VERSION, "Internal S3 Version is too old.")
            
            bulletRes = loads(r.text)
            bulletToken = bulletRes["bulletToken"]
        except Exception:
            return StringResult().statusError(TKError.GET_FAILURE, "Unable to get Bullet Token.")

        token = StringResult()
        token.value = bulletToken
        
        return token.statusOK()
