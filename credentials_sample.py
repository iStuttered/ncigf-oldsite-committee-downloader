import requests

login_url = "[WEBSITE LOGIN URL]"

def generateSession(username:str = "YOUR USERNAME", password:str = "YOUR PASSWORD") -> requests.Session:
    session = requests.Session()
    session.auth = (username, password)
    session.get(login_url)
    return session

def getLoginURL() -> str:
    return login_url