#!/usr/bin/python3
#
# File: intelligent_unit.py
# The unit in charge of choosing a line of questioning
# Copyright 2018
# The Gerrit Group
#

# Test usage
# ~ python3
# >>> iu = IU(udl = <INPUT YOUR UDL HERE>)
# Now you can perform tests on the iu object.

from more_itertools import unique_everseen
from collections import defaultdict, Counter
from random import randint
from config import *

class IU:
    def __init__(self, udl = []):
        """
        Initializes a new IU (intelligent unit) object.
        Its purpose is to choose a line of questioning.

        Input
            udl - stands for URL Dictionary List. This is a list of
                dictionaries either directly from the backend or decreased by
                level or keyword confirmation. There is never a clear winner
                among them at initialization. The dictionaries are sorted by
                likelihood.
        """
        self.udl = udl
        self.history = []
        # TODO was implemented in the conversation class, need to discuss
        self.certain_keywords = set()
        self.confirmed_level = None
        self.wrong_urls = set()

    def choice(self, keywords):
        """
        Makes a choice based on the udl and history of choices and returns this
        choice. Also updates the choice history.

        Input
            keywords - the current keywords stored in the conversation [set]

        Output
            A tuple containing a number corresponding to the chosen action and,
            if applicable, a specific choice of keyword.
            The numbers correspond to the following actions:
                1 - confirm level
                2 - confirm keyword
                3 - extend keyword
                4 - rephrase
                5 - other measures
        """
        output = None
        # 1: confirm level
        contenders = list(range(0, len(self.udl)))
        contenders = self.check_scores(contenders)
        if self.confirmed_level is None:
            level_dict = self.cluster_levels(len(contenders))
            if len(level_dict) != 1:
                output = (1, None)
                self.history.append(output)
                return output
        # 2: confirm keyword
        # REP_CONFIRM configurable for more repeats of the confirm step
        hist_cnt = Counter(self.history)
        rep_conf_list = [k for k, v in hist_cnt.items() if v >= REP_CONFIRM]
        if 2 not in (x[0] for x in rep_conf_list):
            keyword = self.choose_keyword(contenders, keywords)
            if keyword is not None:
                output = (2, keyword)
                self.history.append(output)
                return output
        # 3: extend keyword
        # REP_EXTEND configurable for more repeats of the extend step
        if (3, None) not in [k for k, v in hist_cnt.items() if v >= REP_EXTEND]:
            output = (3, None)
        # 4: rephrase
        elif (4, None) not in self.history:
            output = (4, None)
        # 5: other measures
        else:
            output = (5, None)
            if self.confirmed_level is None:
                output = (1, None)
            elif keywords is not None:
                for kw in keywords:
                    if kw not in self.certain_keywords:
                        output = (2, kw)
        self.history.append(output)
        return output

    def check_scores(self, contenders):
        """
        Checks which dictionaries in self.udl 

        Input - list of indices of self.udl to be checked.

        Output - list of indices from the input list that are higher than the 
            score threshold and also higher than a certain percentage of the 
            highest score found.
        """
        if not self.udl:
            return []
        if self.udl[0]["Score"] >= SCORE_THRESH:
            highest_threshold = max(SCORE_THRESH, SCORE_PERC * self.udl[0]["Score"])
            to_be_removed = []
            for i in contenders:
                if self.udl[i]["Score"] < highest_threshold:
                    to_be_removed.append(i)
            # has to be reversed to be able to remove multiple indices
            for i in to_be_removed[::-1]:        
                contenders.remove(i)
        return contenders

    def choose_keyword(self, contenders, keywords):
        """
        Chooses a keyword included in one of the contenders.
        
        Input
            contenders - list of contending indices
            keywords - In future versions the conversation keywords could be 
                used as well.

        Returns
            Chosen keyword (string)
        """
        chosen_kw = None
        keyword_to_url_indices = defaultdict(list)
        for index in contenders:
            for kw in self.udl[index]:
                if kw not in self.certain_keywords:
                    keyword_to_url_indices[kw].append(index)
        # If a keyword is in every contender's URL dictionary, it doesn't need 
        # to be confirmed
        for kw in list(keyword_to_url_indices):
            if len(keyword_to_url_indices[kw]) == len(contenders):
                keyword_to_url_indices.pop(kw)
        # we want to keep or remove as many urls as possible (rounds down)
        half_of_list = round(len(contenders) / 2) - 1
        # safe initialization, as it will always be less than that
        minimal_distance = len(contenders)
        for kw, index_list in keyword_to_url_indices.items():
            distance = abs(len(index_list) - half_of_list)
            if distance < minimal_distance:
                chosen_kw = kw
        return chosen_kw

    def cluster_levels(self, max_index):
        """
        Returns a dictionary mapping levels to the number of times they occur
        in the udl
        """
        level_dict = defaultdict(list)
        for i in range(0, max_index):
            level_dict[self.udl[i]["Level"]] += [i]
        return level_dict

    def add_to_udl(self, new_udl):
        """
        Adds more dictionaries to the udl. Also sorts them and removes double
        entries. Doesn't add dictionaries with confirmed wrong urls or levels.
        """
        new_udl = [ud for ud in new_udl if ud["URL"] not in self.wrong_urls]
        if self.confirmed_level is not None:
            new_udl = [ud for ud in new_udl if ud["Level"] == self.confirmed_level]
        self.udl = new_udl + self.udl
        self.udl = list(unique_everseen(self.udl))
        self.udl = sorted(self.udl, key=lambda k: k['Score'], reverse=True)

    def remove_url(self, url):
        """
        Removes a wrong URL from the IU.
        """
        removed = False
        for ud in self.udl:
            if ud["URL"] == url:
                self.udl.remove(ud)
                self.wrong_urls.add(url)
                removed = True
        if removed:
            return True
        return False

    def keyword_change(self, keyword, remove=False):
        """
        Confirms or removes a keyword. If a keyword is removed, removes URL
        dictionaries containing it.
        """
        if remove:
            for ud in self.udl:
                if keyword in ud["Keywords"]:
                    self.udl.remove(ud)
        else:
            self.certain_keywords.add(keyword)
        return True

    def level_change(self, level):
        """
        Removes URL dictionaries with levels other than level. Also confirms
        that the level has been checked.
        """
        for ud in self.udl:
            if level == ud["Level"]:
                self.udl.remove(ud)
        self.confirmed_level = level

    def get_winner(self, highest=False):
        """
        If there is a clear winning url in the udl, returns it. Otherwise
        returns None.
        """
        if len(self.udl) == 0:
            return None, None
        if highest:
            return self.udl[0]["URL"], self.udl[0]["Answer"]
        contenders = list(range(0, len(self.udl)))
        contenders = self.check_scores(contenders)
        if len(contenders) == 1:
            return self.udl[contenders[0]]["URL"], self.udl[contenders[0]]["Answer"]
        else:
            return None, None

    def keyword_done(self, keyword):
        if keyword in self.certain_keywords:
            return True
        return False

    def level_done(self):
        if self.confirmed_level is None:
            return False
        return True

    def get_confirmed_level(self):
        return self.confirmed_level

    def get_confirmed_keywords(self):
        return self.certain_keywords

    def get_wrong_urls(self):
        return self.wrong_urls
