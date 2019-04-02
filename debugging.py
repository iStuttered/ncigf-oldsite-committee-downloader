import os, logging, sys

def pause():
    """
    Breakpoint for code tests.
    """
    input(" ----- Pause -----")

def clear():
    """
    A console.clearScreen() for easier console viewing.
    """
    os.system("clear")

def generateLogger() -> logging.Logger:
    logger = logging.getLogger("ncigf-oldsite-committee-downloader")
    logger.setLevel(logging.INFO)

    stream = logging.StreamHandler()
    stream.setLevel(logging.INFO)

    formatter = logging.Formatter("%(levelname)s : %(message)s")

    stream.setFormatter(formatter)

    logger.addHandler(stream)

    return logger