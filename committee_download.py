"""
Member Dev Committees Downloader
V 0.85
NJ

Downloads all of the committee agendas and minutes from the old member's site
and organizes them into folders on the local file system. 

Dependencies:
textract, which does require some fiddling to download all of the required
packages as well as Ubuntu or OSx for the operating system. 
A default output directory like:

parentDirectory:str = "/home/njennings/minutes_pdfs/"

minutes_pdfs is the folder that will house committee folders and then all the
files within each committee within in each folder.

Also make sure to change the username and password immediately below.

"""
import credentials
import re, requests, time, os, shutil, urllib
from time import gmtime, strftime
from bs4 import BeautifulSoup
import textract

session = credentials.generateSession()

def pause():
    """
    Breakpoint for code tests.
    """
    input(" -=-=- Pause -=-=-")

def getLinksFromTaxonomy(href:str) -> list:
    """
    Get all the file links from every page of a paticular taxonomy URL.

    Example: https://member.ncigf.org/taxonomy/term/332
    
    Args:
        href (str): A link to a taxonomy page.
    
    Returns:
        list: A list of file node links.
    """
    page = session.get(href)

    html = BeautifulSoup(page.content, "html.parser")

    lastPage = html.find("a", {"title": "Go to last page"})["href"].split("=")[1]
    
    lastPage = int(lastPage)

    all_links = []

    for pageIndex in range(lastPage + 1):
        print("Parsing page " + str(pageIndex) + " out of " + str(lastPage) + " " + href)

        paginated = session.get(href + "?page=" + str(pageIndex))
        html = BeautifulSoup(paginated.content, "html.parser")
        view_content = html.find("div", {"class": "view-content"})
        links = view_content.find_all("a")
        links = [''.join([loginurl, node["href"]]) for node in links]

        all_links.extend(links)

    return all_links




def getMinutes() -> list:
    """
    Get all the node files from the minutes taxonomy page.
    
    Returns:
        list: A list of node files.
    """
    minutes = "https://member.ncigf.org/taxonomy/term/334"
    return getLinksFromTaxonomy(minutes)

def clear():
    """
    A console.clearScreen() for easier console viewing.
    """
    os.system("clear")


def getAgendas() -> list:
    """
    Get all the node files from the agendas taxonomy page.
    
    Returns:
        list: A list of node files.
    """
    agendas = "https://member.ncigf.org/taxonomy/term/332"
    return getLinksFromTaxonomy(agendas)

def cleanCommitteesFolder(downloadFolder:str = "/home/njennings/minutes_pdfs/"):
    """
    Delete everything in the downloadFolder so the script has a fresh start.

        downloadFolder (str, optional): Defaults to "/home/njennings/minutes_pdfs/". The folder that should be cleaned.
    """
    for the_file in os.listdir(downloadFolder):
        file_path = os.path.join(downloadFolder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path): 
                shutil.rmtree(file_path)
        except Exception as e:
            print(e)
    
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

def buildCommittees(parentDirectory:str = "/home/njennings/minutes_pdfs/"):
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
    
    for committee in committees:
        os.mkdir(parentDirectory + "//" + committee)

def matchTwoDates(file:str) -> str:
    """
    Get other files in the same folder as the given file that have the same
    date in the file name.
    
    Args:
        file (str): A file to match.
    
    Returns:
        str: A list of other files containing the same date as the given file.
    """

    filePieces = file.split("/")

    fileName = filePieces[-1]

    parentDirectory = "/".join(filePieces[0:-1])

    dateOfFirstFile = re.search(r"\d{1,2}(\/|-)\d{1,2}(\/|-)(\d{4}|\d{2})", fileName)
            
    if dateOfFirstFile == None:
        return []

    datePieces = re.split(r",|_|\s|-", dateOfFirstFile.group(0))

    if len(datePieces) != 3:
        return []

    first_month = datePieces[0]
    first_day = datePieces[1]
    first_year = datePieces[2]

    matching_files = []

    for f in os.listdir(parentDirectory):

        dateOfSecondFile = re.search(r"\d{1,2}(\/|-)\d{1,2}(\/|-)(\d{4}|\d{2})", f)

        if dateOfSecondFile != None:

            second_datePieces = re.split(r",|_|\s|-", dateOfSecondFile.group(0))
            second_month = second_datePieces[0]
            second_day = second_datePieces[1]
            second_year = second_datePieces[2]

            if first_month == second_month and first_day == second_day and first_year == second_year and f != fileName:
                matching_files.append("/".join([parentDirectory, f]))

    return matching_files

def monthToInt(month:str) -> str:
    """
    Get the month integer with padding given the month name.
    
    Args:
        month (str): A month in lowercase.
    
    Returns:
        str: A padded integer representing the number of the month.
    """
    months = {
        "january":1,
        "february":2,
        "march":3,
        "april":4,
        "may":5,
        "june":6,
        "july":7,
        "august":8,
        "september":9,
        "october":10,
        "november":11,
        "december":12,
    }

    chosenMonth = months[month.lower()]

    if chosenMonth < 10:
        return str(0) + str(chosenMonth)
    else:
        return str(months[month.lower()])


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

def downloadFile(nodeHREF:str, downloadFolder:str = "/home/njennings/minutes_pdfs/"):
    """
    Given a node link, download the actual file that belongs to the link and
    place it in the downloadFolder.
    
    Args:
        nodeHREF (str): A node link. Ex: https://member.ncigf.org/node/3544
        downloadFolder (str, optional): Defaults to
    "/home/njennings/minutes_pdfs/". The folder to which the file will be placed.  
    """
    page = session.get(nodeHREF)
    html = BeautifulSoup(page.content, "html.parser")
    message_status = html.find("div", {"class": "messages status"})
    href = message_status.find("a")["href"]

    if loginurl not in href:
        href = loginurl + href

    downloadRequest = session.get(href, allow_redirects=True)

    localPath = downloadFolder + href.split("/")[-1]

    if "draft" in localPath.split("/")[-1].lower():
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





        



    
