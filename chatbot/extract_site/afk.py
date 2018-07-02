#!/usr/bin/python3
#
# File: afk.py
# Scrape abbreviations from the UvA site
# Copyright 2018
# The Gerrit Group
#

# (Test) usage
# Call:
# python3 afk.py
# OR
# python3 afk.py "http://student.uva.nl/opleidingen/opleidingenlijst.html" "afk_nl.txt"
# python3 afk.py "http://student.uva.nl/en/study-programmes/study-programmes.html" "afk_en.txt"

from bs4 import BeautifulSoup
import requests, sys

def get_soup(url):
    """
        Generates a BeautifulSoup instance for a url
        Input:
            url: str
        Output:
            b: BeautifulSoup | None
    """
    try:
        b = BeautifulSoup(requests.get(url).text, "lxml")
    except:
        print("Server Error")
        b = None
    return b

def get_afk(url, dest):
    """
        Generate the list of afkortingen
        Input:
            url: str
            dest: str
        Outpt:
            writes str(dict) to dest
    """
    s = get_soup(url)
    if s != None:
        afk = {}
        for link in s.find_all('a'):
            c = link.get('class')
            if c and c[0] == "icon-arrow":
                afk[link.get('href').split('/')[-1]] = link.text

        with open(dest, 'w') as file:
            print("--- Writing to", dest)
            file.write(str(afk))

# Handle input
if __name__ == "__main__":
    if len(sys.argv) <= 2:
        # Standard
        print("Getting NL AFK")
        get_afk("http://student.uva.nl/opleidingen/opleidingenlijst.html",
                "afk_nl.txt")
        print("Getting EN AFK")
        get_afk("http://student.uva.nl/en/study-programmes/study-programmes.html",
                "afk_en.txt")
        print("Finished")
    else:
        get_afk(sys.argv[1], sys.argv[2])
