import requests

login_url = "[WEBSITE LOGIN URL]"
base_url = "[WEBSITE BASE URL]"
username = "[YOUR USERNAME]"
password = "[YOUR PASSWORD]"
committees_directory = "[COMMITTEES ROOT DIRECTORY]"

def generateSession() -> requests.Session:
    session = requests.Session()
    session.auth = (username, password)
    session.get(login_url)
    return session

def getLoginURL() -> str:
    return login_url

def getBaseURL() -> str:
    return base_url

def getCommitteesDirectory() -> str:
    return committees_directory