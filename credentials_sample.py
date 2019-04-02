import requests, os

login_url = "[WEBSITE LOGIN URL]"
base_url = "[WEBSITE BASE URL]"
username = "[YOUR USERNAME]"
password = "[YOUR PASSWORD]"
committees_directory = "[COMMITTEES ROOT DIRECTORY]"

def generateSession() -> requests.Session:
    session = requests.Session()
    session.auth = (username, password)

    max_retries = 3
    backoff_increment = 1

    retries = Retry(
        total=max_retries,
        read=max_retries,
        connect=max_retries,
        backoff_factor=backoff_increment,
        status_forcelist=(500, 502, 504)
    )

    adapter = HTTPAdapter(max_retries=retries)

    session.mount("http://", adapter)
    session.mount("https://", adapter)

    session.verify = False


    session.get(login_url)

    return session

def getBaseURL() -> str:
    return base_url

def getCommitteesDirectory() -> str:
    
    current_directory = os.path.dirname(os.path.realpath(__file__))

    committees_directory = current_directory + "/minutes_pdfs/"
    
    return committees_directory