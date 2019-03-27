import credentials, debugging
import re, requests, time, os, shutil, urllib
from time import gmtime, strftime
from bs4 import BeautifulSoup
import textract

session = credentials.generateSession()

def getLinksFromTaxonomy(page_href:str) -> list:
    """
    Get all the file links from every page of a paticular taxonomy URL.

    Example: https://member.ncigf.org/taxonomy/term/332
    
    Args:
        href (str): A link to a taxonomy page.
    
    Returns:
        list: A list of file node links.
    """
    page = session.get(page_href)

    html = BeautifulSoup(page.content, "html.parser")

    last_page_element = html.find("a", {"title": "Go to last page"})

    last_page_href = last_page_element["href"]

    last_page = last_page_href.split("=")[1]
    
    last_page = int(last_page)

    documents = []

    base_html_url = credentials.getBaseURL()

    for pageIndex in range(last_page + 1):

        print("Parsing page " + str(pageIndex) + " out of " + str(last_page) + " " + page_href)

        paginated_page = session.get(page_href + "?page=" + str(pageIndex))
        paginated_html = BeautifulSoup(paginated_page.content, "html.parser")

        view_content_element = paginated_html.find("div", {"class": "view-content"})

        document_links = view_content_element.find_all("a")

        document_links = [
            ''.join( [base_html_url, element["href"]] ) for element in document_links
        ]

        documents.extend(document_links)

    return documents

def getMinutes() -> list:
    """
    Get all the node files from the minutes taxonomy page.
    
    Returns:
        list: A list of node files.
    """
    minutes = "https://member.ncigf.org/taxonomy/term/334"
    return getLinksFromTaxonomy(minutes)

def getAgendas() -> list:
    """
    Get all the node files from the agendas taxonomy page.
    
    Returns:
        list: A list of node files.
    """
    agendas = "https://member.ncigf.org/taxonomy/term/332"
    return getLinksFromTaxonomy(agendas)

def cleanCommitteesFolder():
    """
    Delete everything in the downloadFolder so the script has a fresh start.

    """

    committees_directory = credentials.getCommitteesDirectory()

    for file_name in os.listdir(committees_directory):
        dir_path = os.path.join(committees_directory, file_name)
        try:
            if os.path.isfile(dir_path):
                os.unlink(dir_path)
            elif os.path.isdir(dir_path): 
                shutil.rmtree(dir_path)
        except:
            print("Could not clean old directory.")
    
def downloadTaxonomy(taxonomyLinks:list):
    """
    Download all of the taxonomy links in the given list as well as organize
    them by committee.
    
    Args:
        taxonomyLinks (list): A list of node files retrieved from a taxonomy page.
    """
    index = 1
    total = len(taxonomyLinks)
    for link in taxonomyLinks:
        organizeFile(link)
        print(str(index) + "/" + str(total))
        index += 1

def buildCommittees():
    """
    Create a folder for every committee and place the folder inside
    parentDirectory.
    
        parentDirectory (str, optional): Defaults to "/home/njennings/minutes_pdfs/". A directory to place committee folders into.
    """
    committees = [
        "Accounting Issues Committee",
        "Best Practices Committee",
        "Audit Committee",
        "Corporate Governance",
        "Finance Committee",
        "Bylaws Committee",
        "Communications Committee",
        "Coordinating Committee Chairs Committee",
        "Core Services Committee",
        "Education Committee",
        "Information Systems Committee",
        "IT Advisory",
        "Legal Committee",
        "Member Committee Advisory Committee",
        "NCIGF Services Committee",
        "Nominating Committee",
        "Operations Committee",
        "Public Policy Committee",
        "Site Selection Committee",
        "Special Funding Committee"
    ]

    committee_directory = credentials.getCommitteesDirectory()
    
    for committee in committees:
        os.mkdir(committee_directory + "//" + committee)

def determineCommittee(file:str):
    """
    Use Textract to convert a given PDF file to text and get the committee that
    file likely belongs. 
    
    Args:
        file (str): A PDF file to process.
    """

    text = None

    try:
        text = textract.process(file).splitlines()
    except:
        return
    
    committees = [
        "Accounting Issues Committee",
        "Best Practices Committee",
        "Audit Committee",
        "Corporate Governance",
        "Finance Committee",
        "Bylaws Committee",
        "Communications Committee",
        "Coordinating Committee Chairs Committee",
        "Core Services Committee",
        "Education Committee",
        "Information Systems Committee",
        "IT Advisory",
        "Legal Committee",
        "Member Committee Advisory Committee",
        "NCIGF Services Committee",
        "Nominating Committee",
        "Operations Committee",
        "Public Policy Committee",
        "Site Selection Committee",
        "Special Funding Committee"
    ]

    for line in text:
        for committee in committees:
            if committee.lower() in str(line.strip().lower(), "utf-8"):
                return committee + "/"
    
    return None

def downloadFile(nodeHREF:str):
    """
    Given a node link, download the actual file that belongs to the link and
    place it in the downloadFolder.
    
    Args:
        nodeHREF (str): A node link. Ex: https://member.ncigf.org/node/3544
        downloadFolder (str, optional): Defaults to
    "/home/njennings/minutes_pdfs/". The folder to which the file will be placed.  
    """
    request = session.get(nodeHREF)
    page_html = BeautifulSoup(request.content, "html.parser")
    message_status_element = page_html.find("div", {"class": "messages status"})
    file_href = message_status_element.find("a")["href"]

    base_html_url = credentials.getBaseURL()

    if base_html_url not in file_href:
        file_href = base_html_url + file_href

    downloadRequest = session.get(file_href, allow_redirects=True)

    committee_directory = credentials.getCommitteesDirectory()

    file_name = file_href.split("/")[-1]

    localPath = committee_directory + file_name

    if "draft" in file_name.lower():
        print("Ignore drafts.")
        return

    try:
        open(localPath, mode="wb").write(downloadRequest.content)
        return localPath
    except OSError:
        print("Failed to download.")
        return

def organizeFile(file:str, downloadFolder:str = "/home/njennings/minutes_pdfs/") -> str:
    """
    Attempt to retrieve the committee to which the file belonged and place it
    under the associated committee folder.
    
    Args:
        file (str): A file path to organize.
        downloadFolder (str, optional): Defaults to
    "/home/njennings/minutes_pdfs/". A folder to put the downloaded file
    preemptively before organizing.
    
    Returns:
        str: [description]
    """

    localPath = downloadFile(file)

    if localPath == None:
        return

    if "doc" in localPath.split('.')[1] or "msg" in localPath.split('.')[1]:
        print("Not a valid file format.")
        return

    committee = determineCommittee(localPath)

    if committee == None:
        return

    fileName = localPath.split("/")[-1]
    fileName = downloadFolder + committee + localPath.split("/")[-1].split(".")[0] + ".txt"
    if committee != None:
        with open(fileName, "wb") as f:
            text = textract.process(localPath).splitlines()
            f.writelines(text)
            os.remove(localPath)

        return fileName
    else:
        print("Could not determine committee.")
        return

def main():
    """
    The main method which does the following:
    1. Clean the output folder
    2. Rebuild the output folder directories
    3. Get a list of links of all the agendas and minutes
    4. Download those links and organize them into committees
    """
    print(" - - - Start - - - ")
    cleanCommitteesFolder()
    buildCommittees()
    agendas = getAgendas()
    minutes = getMinutes()
    downloadTaxonomy(agendas)
    downloadTaxonomy(minutes)
    print(" - - - End - - - ")

main()





        



    
