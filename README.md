NCIGF Committees Downloader
---------------------------
This repository is for downloading and organizing committee files from the old member's site of NCIGF.

The script requires a credentials.py file located in the root directory of the repository. 

_____________________________________
import requests

def generateSession(login_url:str = "[YOUR URL]", username:str = "[YOUR USERNAME]", password:str = [YOUR PASSWORD]):
    session = requests.Session()
    session.auth = (username, password)
    session.get(login_url)
    return session
_____________________________________
