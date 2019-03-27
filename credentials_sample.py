import requests

def generateSession(login_url:str = "[WEBSITE LOGIN URL]", username:str = "YOUR USERNAME", password:str = "YOUR PASSWORD"):
    session = requests.Session()
    session.auth = (username, password)
    session.get(login_url)
    return session