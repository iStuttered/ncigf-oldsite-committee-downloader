import credentials, debugging, re, requests, time, os, shutil, urllib3, textract
from bs4 import BeautifulSoup
from pathlib import Path

logger = debugging.generateLogger()
session = credentials.generateSession()

def deleteHistory():
    """
    Delete the links_history archive file.
    
    """

    committee_folder = credentials.getCommitteesDirectory()

    links_history_file = committee_folder + "../links_history.txt"

    if os.path.exists(links_history_file):
        os.unlink(links_history_file)

def saveLinksFromTaxonomy(links:list):
    """
    Save links retrieved from getLinksFromTaxonomy into a links_history file.
    
    Parameters
    ----------
    links : list
        A list of links.
    
    """


    committee_folder = credentials.getCommitteesDirectory()

    links_history_file = committee_folder + "../links_history.txt"

    with open(links_history_file, "a") as history_file:

        links = ("".join([link, "\n"]) for link in links)

        history_file.writelines(links)

def getLinksFromHistory() -> list:
    """
    Get file links from links_history file.
    
    Returns
    -------
    list
        A list of links.
    """

    committee_folder = credentials.getCommitteesDirectory()

    links_history_file = committee_folder + "../links_history.txt"

    history_links = []

    with open(links_history_file, "r") as history_file:

        for link in history_file:

            cleaned_link = link.strip()

            if len(cleaned_link) > 0:
                history_links.append(link.strip())

    return history_links

def getLinksFromTaxonomy(page_href:str) -> list:
    """
    Get all the file links from every page of a paticular taxonomy URL.

    Example: https://member.ncigf.org/taxonomy/term/332
    
    Args:
        href (str): A link to a taxonomy page.
    
    Returns:
        list: A list of file links.
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

        logger.info("Parsing page " + str(pageIndex) + " out of " + str(last_page) + " " + page_href)

        paginated_page = session.get(page_href + "?page=" + str(pageIndex))

        paginated_html = BeautifulSoup(paginated_page.content, "html.parser")

        view_content_element = paginated_html.find("div", {"class": "view-content"})

        node_links = view_content_element.find_all("a")

        node_links = [
            ''.join( [base_html_url, element["href"]] ) for element in node_links
        ]

        for node_link in node_links:

            file_request = session.get(node_link)

            page_html = BeautifulSoup(file_request.content, "html.parser")

            tabs_wrapper = page_html.find("div", {"id": "squeeze"})

            message_status_element = tabs_wrapper.find("div", {"class": "messages status"})

            file_href = message_status_element.find("a")["href"]

            if base_html_url not in file_href:
                file_href = base_html_url + file_href

            documents.append(file_href)

    saveLinksFromTaxonomy(documents)

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

def getBoardMinutes() -> list:
    board_minutes = "https://member.ncigf.org/board_members/board_minutes"
    return getLinksFromTaxonomy(board_minutes)

def cleanCommitteesFolder():
    """
    Delete everything in the downloadFolder so the script has a fresh start.

    """
    committees_directory = credentials.getCommitteesDirectory()

    if not os.path.exists(committees_directory):
        return None

    committee_folders = os.listdir(committees_directory)

    for committee_folder in committee_folders:

        committee_folder_path = os.path.join(committees_directory, committee_folder)

        if os.path.isfile(committee_folder_path):
            os.unlink(committee_folder_path)
            continue

        for committee_file_name in os.listdir(committee_folder_path):

            committee_file_path = os.path.join(committee_folder_path, committee_file_name)
            
            try:
                if os.path.isfile(committee_file_path):

                    os.unlink(committee_file_path)

                elif os.path.isdir(committee_file_path): 
                    
                    shutil.rmtree(committee_file_path)
            except:
                logger.error("Could not clean old directory.")


def downloadTaxonomy(taxonomyLinks:list):
    """
    Download all of the taxonomy links in the given list as well as organize
    them by committee.
    
    Args:
        taxonomyLinks (list): A list of node files retrieved from a taxonomy page.
    """       

    files_organized = 0
    total_files = len(taxonomyLinks)
    for link in taxonomyLinks:

        organized_file = organizeFile(link)

        if organized_file == None:
            continue

        organized_file_name = organized_file.split("/")[-1]

        if len(organized_file) > 0:
            files_organized += 1
            logger.info(str(files_organized) + "/" + str(total_files) + " " + organized_file_name)
        else:
            logger.warning("File was not organized.")

def buildCommittees():
    """
    Create a folder for every committee and place the folder inside
    committee_directory defined in the credentials file.
    """
    committee_names = [
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
    
    for committee_name in committee_names:
        committee_subfolder = Path(committee_directory + "/" + committee_name)
        committee_subfolder.mkdir(parents=True, exist_ok="True")

def determineCommittee(lines_in_file:str):
    """
    Use Textract to convert a given PDF file to text and get the committee that
    file likely belongs. 
    
    Args:
        file (str): A PDF file to process.
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

    for line in lines_in_file:
        for committee in committees:
            if committee.lower() in str(line.strip().lower(), "utf-8"):
                return committee + "/"
    
    return None

def downloadFile(file_href:str):
    """
    Given a node link, download the actual file that belongs to the link and
    place it in the downloadFolder.
    
    Args:
        nodeHREF (str): A node link. Ex: https://member.ncigf.org/node/3544
        downloadFolder (str, optional): Defaults to
    "/home/njennings/minutes_pdfs/". The folder to which the file will be placed.  
    """

    try: 
        file_request = session.get(file_href, allow_redirects=True, stream=True)
    except urllib3.util.ssl_.SSLError:
        logger.error("Download failed. Something went wrong with requesting the file.")

    committee_directory = credentials.getCommitteesDirectory()

    file_name = file_href.split("/")[-1]

    local_path = committee_directory + file_name

    if "draft" in file_name.lower():
        logger.warning("Download failed. Ignoring files with 'draft' in the name.")
        return None

    try:
        with open(local_path, mode="wb") as local_file:
            for file_chunk in file_request.iter_content(chunk_size=1024):
                if file_chunk:
                    local_file.write(file_chunk)

            if os.path.getsize(local_path) > 1:
                return local_path
            else:
                logger.warning("Downloaded file will not be moved due to its tiny size.")
                return None
    except OSError:
        logger.warning("Failed to move file to committee. " + local_path)
        return None

def organizeFile(file_path:str):
    """
    Attempt to retrieve the committee to which the file belonged and place it
    under the associated committee folder.
    
    Args:
        file (str): A file path to organize.
    
    Returns:
        str: An absolute file path
    """
    local_file_path = downloadFile(file_path)

    if local_file_path == None:
        return None

    local_file_name = local_file_path.split("/")[-1]
    local_file_name_no_extension = local_file_name.split(".")[0]
    committee_directory = credentials.getCommitteesDirectory()

    local_file_pieces = local_file_name.split(".")

    local_file_name_extension = None
    
    if len(local_file_pieces) > 1: 
        local_file_name_extension = local_file_pieces[-1]
    else:
        logger.warning(local_file_name + " Couldn't find file extension")
        return None

    invalid_extensions = ["msg", "doc"]

    if any(extension.lower() in local_file_name_extension for extension in invalid_extensions):
        logger.warning(local_file_name + " [" + local_file_name_extension + "] Not a valid file format")
        return None

    processed_text = None

    try:
        processed_text = textract.process(local_file_path)
    except Exception:
        logger.warning(local_file_name + " couldn't be processed into text")
        return None

    lines_in_local_file = processed_text.splitlines()

    committee_name = determineCommittee(lines_in_local_file)

    if committee_name == None:
        logger.warning(local_file_name + " Could not determine committee")
        return None
    else:
        new_file_path_txt = committee_directory + committee_name + local_file_name_no_extension + ".txt"
        new_file_path_pdf = committee_directory + committee_name + local_file_name_no_extension + ".pdf"

        with open(new_file_path_txt, "wb") as new_file:
            new_file.write(processed_text)
            os.rename(local_file_path, new_file_path_pdf)

        return new_file_path_txt

def userWantsToLoadLinksFromHistory() -> bool:
    response = input("Load links from history, instead of from the internet? (Y/n)").strip().lower()
    return response == "y" or len(response) < 1


if __name__ == "__main__":
    """
    The main method which does the following:
    1. Clean the output folder
    2. Rebuild the output folder directories
    3. Get a list of links of all the agendas and minutes
    4. Download those links and organize them into committees
    """
    logger.info(" - - - Start - - - ")
    cleanCommitteesFolder()
    buildCommittees()

    if userWantsToLoadLinksFromHistory():
        agendas_minutes = getLinksFromHistory()
        downloadTaxonomy(agendas_minutes)
    else:
        deleteHistory()
        agendas = getAgendas()
        minutes = getMinutes()
        board_minutes = getBoardMinutes()
        downloadTaxonomy(agendas)
        downloadTaxonomy(minutes)
        downloadTaxonomy(board_minutes)
    logger.info(" - - - End - - - ")

