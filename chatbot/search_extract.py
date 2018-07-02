import requests
from bs4 import BeautifulSoup

def backend_end_alternative(server_dictionary):
    """
    Input
        dictionary from conversation
    Output
        list of url dictionaries
    """
    link_list = search_extract(server_dictionary["Keywords"], server_dictionary["Language"], 5)
    if link_list is None:
        return None
    udl = []
    score = 1
    for link in link_list:
        new_dict = {"URL": link, "Score": score, "Level": server_dictionary["Level"], "Keywords": set(), "Answer": "<i><p>A nice answer.</p><p>Maybe multiple lines!</p><i>"}
        score -= score * 0.4
        udl.append(new_dict)
    # print(udl)
    return udl

def search_extract(keywords, language, max_links):
    if language == 0:
        start_link = "http://www.uva.nl/search?q="
    elif language == 1:
        start_link = "http://www.uva.nl/en/search?q="
    first = True
    for keyword in keywords:
        if not first:
            start_link += '+'
        first = False
        start_link += keyword
    try:
        start_page = requests.get(start_link)
    except:
        return None
        # raise ConnectionError("Connection with the UvA website seems to have failed.")
    soup = BeautifulSoup(start_page.content, 'html.parser')
    link_list = []
    for i, soupTag in enumerate(soup.findAll('a', attrs={"class": "action"})):
        if i >= max_links:
            break
        link = soupTag.get('href')
        link_list.append(link)
    return link_list
        

if __name__ == "__main__":
    search_extract({"studieadviseur", "ki"}, 1, 5)