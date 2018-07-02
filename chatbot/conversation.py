#!/usr/bin/python3
#
# File: conversation.py
# The main class for a chatbot conversation
# Copyright 2018
# The Gerrit Group
#

# (Test) usage
# ~ python3 conversation.py "sentence"

# Imports
import nltk
import sys
from nltk.metrics import *
import ast

from config import *


class Conversation:
    def __init__(self, sentence):
        """
            Initialise a conversation with a sentence

            Input
                sentence (str)
        """
        self.set_types()
        self.main_string   = sentence
        self.main_language = Conversation.language(sentence)
        self.stopwords     = self.set_all_stopwords()
        self.extract       = "extract_site/"
        self.studies       = self.set_all_studies()
        self.sentences     = [Sentence(sentence, self, self.main_language)]
        self.keywords      = set()
        self.set_conversation_keywords(self.sentences[0])
        self.set_level(self.sentences[0].get_level())

        # Init confirmations
        self.confirmed_keywords = set()
        self.confirmed_level = False
        self.confirmed_reformed = False

    def add_sentence(self, sentence):
        """
            Add a sentence to the conversation
            Input
                sentence (str)
        """
        self.sentences += [Sentence(sentence, self)]

    def add_rephrase(self, sentence):
        rephrase = Sentence(sentence, self)
        self.sentences += [rephrase]
        self.main_string = sentence
        self.set_conversation_keywords(rephrase)

    def get_sentences(self):
        """
            Returns the sentences in the conversation
            Output:
                sentences: set
        """
        return self.sentences

    def set_types(self, D=None):
        """
            Define the types
            Input:
                D: dict
            Output:
                bool
        """
        # Nog geen check op type van D

        # Hardcoded, language detection not needed
        if D == None:
            D = {1: {'wie', 'who'},
                 2: {'what', 'wat', 'whut'},
                 3: {'where', 'waar', 'war'},
                 4: {'why', 'wy', 'waarom', 'wrm', 'warom', 'waarrom'},
                 5: {'when', 'wen', 'wanneer', 'waneer', 'wanner'},
                 6: {'how', 'hoe'},
                 7: {'which', 'welke'}
                 }
        self.types = D
        return True

    def get_types(self):
        """
            Returns the types
            Output:
                self.types: dict
        """
        return self.types

    def get_last_sentence(self):
        """
            Returns the last sentence in the conversation
        """
        return self.sentences[-1]

    def set_conversation_keywords(self, keywords):
        """
            Generate the keywords for a conversation
            Input:
                keywords: Sentence or str
        """
        if isinstance(keywords, Sentence):
            self.keywords |= keywords.get_keywords()
        else:
            self.keywords |= {keywords}

    def get_conversation_keywords(self):
        """
            Return the keywords for a conversation
            Output: keywords (set)
        """
        return self.keywords

    def remove_conversation_keywords(self, keywords):
        """
            Generate the keywords for a conversation
            Input:
                keywords: Sentence or str
        """
        if isinstance(keywords, Sentence):
            self.keywords -= keywords.get_keywords()
        else:
            self.keywords -= {keywords}

    def confirm_keyword(self, keyword: str):
        """
            Add confirmed keyword
            Input:
                keyword: str
        """
        self.confirmed_keywords |= {keyword}

    def get_confirmed_keywords(self):
        """
            Returns the confirmed keywords in a conversation
            Output:
                confirmed_keywords: set
        """
        return self.confirmed_keywords

    def get_main_language(self):
        """
            Returns the main language
            Output:
                main_language: tuple
        """
        return self.main_language

    def set_main_language(self, lang: tuple):
        """
            Override the initial language
            input:
                Lang: tuple
        """
        self.main_language = lang

    def get_server_dictionary(self):
        """
            Generate a dictonary for a server call
            Returns:
                dict
        """
        return {'Language' : self.main_language[0],
                'Type'     : self.sentences[-1].get_type()[0],
                'Level'    : self.level,
                'Keywords' : self.get_conversation_keywords(),
                'Source'   : self.main_string
               }


    def __str__(self):
        d = {'lang': self.main_language[1], 'sent': len(self.sentences),
             'key': len(self.get_conversation_keywords()),
             'sd': self.get_server_dictionary()}
        s = """
| Conversation\n\
|\n\
| Language: {lang}\n\
| Sentences: {sent}\n\
| Keywords: {key}\n\
| Server Dict: {sd}\n\
            """
        return s.format(**d)

        print("| Conversation\n|\n| Language", self.main_language)

    def set_level(self, level):
        """
            Set the level of the conversation
            Input:
                level: str
        """
        self.level = level

    def get_level(self):
        """
            Get the level of the Conversation
            Output:
                level: str
        """
        return self.level

    def confirm_level(self):
        """
            Confirm level
        """
        self.confirmed_level = True

    def level_confirmed(self):
        """
            Get whether a level is confirmed
            Returns:
                confirmed_level: bool
        """
        return self.confirmed_level

    def reform(self):
        """
            Set reformed op True
        """
        self.confirmed_reformed = True

    def is_reformed(self):
        """
            Return whether we let the user reform already
            Output:
                confirmed_reformed: bool
        """
        return self.confirmed_reformed

    def set_all_stopwords(self):
        """
            Creates a dictionary with language as key and a set of all stopwords
            for that given language.
            For the Dutch nltk we add additional stopwords from a file
        """
        stopwords = {}
        dutch_stopwords = set()
        with open('stopwoorden.txt') as f:
            for line in f:
                dutch_stopwords.add(line)
        nltk_dutch = set(nltk.corpus.stopwords.words('dutch'))
        stopwords['dutch'] = dutch_stopwords.union(nltk_dutch)
        stopwords['english'] = set(nltk.corpus.stopwords.words('english'))
        return stopwords

    def get_stopwords(self, language):
        """
            Input: either 'dutch' or 'english'
            Output: only the stopwords for the desired language
        """
        return self.stopwords[language]

    def extract_from_file(self, filename):
        with open(self.extract+filename, 'r') as file:
            reader = file.readlines()
            all_lines = set([line for line in reader])
        return all_lines

    def read_dict(self, filename):
        abbr_dict = {}
        with open(self.extract+filename, 'r') as file:
            reader = file.readlines()
            dictstring = reader[0]
            abbr_dict = ast.literal_eval(dictstring)
        return abbr_dict

    def set_all_studies(self):
        studict = self.read_dict('faculty_studies.txt')

        all_studies = set()
        for value in studict.values():
            for item in value:
                all_studies.add(item)

        faculty_studies = {}
        faculty_studies['studies'] = all_studies

        abbr_studies = self.read_dict('afk_en.txt')
        abbr_studies = dict(abbr_studies,**(self.read_dict('afk_nl.txt')))

        faculty_studies['abbr_stu'] = abbr_studies

        faculties = self.extract_from_file('faculties_eng.txt')
        faculties = faculties.union(self.extract_from_file('faculties_dut.txt'))

        faculty_studies['faculties'] = faculties

        return faculty_studies

    def get_studies(self, language):
        """
            Input: either 'dutch' or 'english'
            Output: only the studies/faculties for the desired language
        """
        return self.studies[language]

    def language(text):
        # @staticmethod
        """
            Define the language of a text (Dutch/English)
            Source: https://stackoverflow.com/questions/3182268/nltk-and-language-detection
            Input:
                text: str
            Output:
                language: tuple of int and str
        """
        english_vocab = set(w.lower() for w in nltk.corpus.words.words()) | {NAME.lower()}
        text_vocab = set(w.lower() for w in text.split(' ') if w.lower().isalpha())
        diff = text_vocab.difference(english_vocab)
        if (len(diff) / len(text.split(' '))) < 0.2:
            return (1, "English")
        return (0, "Dutch")


class Sentence:
    def __init__(self, sentence, conv, language=None):
        """
            Initialise a Sentence with a sentence
            Input:
                sentence: str
        """
        self.set_string(sentence)
        self.conversation = conv
        if language == None:
            self.set_language()
        else:
            self.language = language
        self.set_type()
        self.set_keywords(conv)
        self.set_level()

    # STRING
    def set_string(self, text):
        """
            Set the string of the sentence
            Input:
                text: str
        """
        self.string = text

    def get_string(self):
        """
            Return the string of the sentence
            Output:
                string: str
        """
        return self.string

    # LANGUAGE
    def set_language(self):
        """
            Set the language of the sentence
        """
        self.language = Conversation.language(self.string)

    def get_language(self):
        return self.language

    # TYPE
    def set_type(self):
        """
            Return the type of a text according to self.types
            Output:
                bool
        """
        text = set(nltk.word_tokenize(self.string.lower()))
        for key, value in Conversation.get_types(self.conversation).items():
            if len(value.intersection(text)) > 0:
                self.type = (key, value)
                return True
        self.type = (0, "Unknown")
        return True

    def get_type(self):
        """
            Return the type of a the sentence
            Output:
                type: tuple
        """
        return self.type

    def calc_score(self, word1, word2):
        """
            Calculate the score of matching two words with double bigram
            approach.
            Input:
                word1: string
                word2: string
            Output:
                score: the similarity score of the words
        """
        score = 0
        for i in range(len(word1)):
            # Max typographical error of 1
            for k in range(-1,2):
                if i<len(word2)-k and i+k>=0:
                    if word1[i] == word2[i+k]:
                        score += 1
                        break
        return score

    def check_sim(self, checkstring, study, thresh, studyname):
        """
            Checks the similarity of combinations of the study with the input
            Input:
                checkstring: string of a given combination of input
                study: string with the stripped studyname
                thresh: int of the threshold
                studyname: string of the full name of the given study
        """
        studysplit = study.split(" ")
        best_mscore = 0
        for h in range(len(studysplit)):
            word = "".join(studysplit[h:])
            mscore = self.calc_score(checkstring,word)
            if mscore > best_mscore:
                best_mscore = mscore

        # Test if one of the words of the study is actually in the query
        best_Tscore = 0
        best_ratio = 0
        for studyword in studysplit:
            Tscore = 0
            Tscore = self.calc_score(studyword,checkstring)
            if Tscore > best_Tscore:
                best_ratio = Tscore/len(studyword)
                best_Tscore = Tscore
        if best_ratio>thresh:
            return best_mscore/(len(studyname.split("(")[0]))
        return 0

    def double_bigram(self, check_list, thresh=BIGRAM_THRESH):
        """
            Extract the level of the sentence using a max typographical error
            distance of 1.
            Input:
                check_list: list of items to be compared
                thresh: threshold whether a match is good enough
        """
        best_matches = []
        for i in range(len(self.keywords)):
            checkstring = ""
            for j in range(i,len(self.keywords)):
                checkstring += self.keywords[j]
                for study_tup in check_list:
                    study = study_tup[0]
                    if len(checkstring)*thresh < len(study):
                        check_study = study.lower()
                        checkstring = checkstring.lower()
                        score = self.check_sim(checkstring,check_study,thresh,study_tup[1])
                        if score > thresh:
                            best_matches.append((study_tup[1],score))
        return best_matches

    def extract_level(self, check_list, thresh=STUDY_THRESH):
        """
            Extract the level of the sentence by comparing the keywords
            of the sentence with all items of a given list
            Input:
                kw: list of keywords of the sentence
                thresh: threshold whether a match is good enough
                check_list: list of items to be compared
            Output:
                best_matches: list of tuples of matched studies and score
        """
        best_matches = []
        # Check everything to be checked
        for check in check_list:
            score = 0
            # Clean every instance of the checklist
            checklist = check.split("(")
            s = len(checklist)
            if len(checklist) > 1:
                s = -1
            checkclean = [x for x in
                            nltk.word_tokenize("".join(checklist[:s]).lower())
                            if len(x) != 1 and "'" not in x and x != 'der']
            # If a keyword of the sentence is found in the
            # instance, increment score
            for word in self.keywords:
                if word in checkclean:
                    score += 1
            # Calculate the score of this instance
            if len(checkclean) == 0:
                word_score = 0
            else:
                word_score = score/len(checkclean)
            # Add the instance and score to good matches if it exceeds threshold
            if word_score > thresh:
                best_matches.append((check,word_score))
        return best_matches

    def lookup_abbr(self, all_abbr):
        """
            Match the user input with the abbreviations of studynames
            Input:
                all_abbr: a dictionary of all the abbreviations of studynames
            Ouput:
                best_matches: a list with a tuple of the matched study with a
                                score of 1
        """
        best_matches = []
        for word in self.keywords:
            if len(word) <= 7:
                if word in all_abbr:
                    best_matches.append((all_abbr[word],1))
        return best_matches

    def match_input_string(self, check_list, thresh=NAIVE_THRESH):
        """
            Match the whole user input with the study
            Input:
                check_list: list of items to be compared
                thresh: threshold whether a match is good enough
            Output:
                best_matches: list of tuples of matched studies and score
        """
        best_matches = []
        for check in check_list:
            points = edit_distance(self.get_string().lower(), check.lower())
            score = 1-points/max(len(self.get_string()),len(check))
            if score > thresh:
                best_matches.append((check,score))
        return best_matches

    # LEVEL
    def set_level(self):
        """
            Set the level of the sentence, being either a study or a faculty
            Input:
                thresh: the threshold to match user input with studies
        """
        level = None

        # Use the list of the given language
        all_studies = self.conversation.studies['studies']
        all_faculties = self.conversation.studies['faculties']
        all_stu_abbr = self.conversation.studies['abbr_stu']

        # Check the input with those lists
        best_matches = self.match_input_string(all_faculties)
        if not best_matches:
            best_matches = self.match_input_string(all_studies)
        if not best_matches:
            best_matches = self.lookup_abbr(all_stu_abbr)
        if not best_matches:
            best_matches = self.extract_level(all_faculties)
        if not best_matches:
            best_matches = self.extract_level(all_studies)

        # If no level could be extracted using the naive functions
        if not best_matches:
            all_clean_studies = [(" ".join([x for x in
                nltk.word_tokenize(" ".join(item.lower().split("(")[:-1])) if
                len(x) > 3 and "'" not in x]),item) for item in all_studies]

            all_clean_faculties = [(" ".join([x for x in
                nltk.word_tokenize(item.lower()) if len(x) > 3 and "'" not in
                x]),item) for item in all_faculties]

            best_matches = self.double_bigram(all_clean_faculties)
            if not best_matches:
                best_matches = self.double_bigram(all_clean_studies)

        # Save the level with the highest score
        if best_matches:
            best_matches.sort(key=lambda tup: tup[1], reverse=True)
            level = best_matches[0][0].replace('\n','')

        print("Found level: ", level)
        self.level = level

    def get_level(self):
        """
            Return the level of the sentence
            Output:
                level: str
        """
        return self.level

    # KEYWORDS
    def set_keywords(self, conv):
        """
            Get the keywords of the sentence
        """
        tokens = {'NOUN', 'ADJ', 'NUM'}
        l = self.language[1].lower()
        sentence = self.string.lower()
        tokenized = nltk.word_tokenize(sentence)
        stopwords = conv.get_stopwords(l)
        tagged = nltk.pos_tag([x for x in tokenized if x not in stopwords],
                              tagset='universal', lang=l)
        print("####")
        print(tagged)
        print("####")
        self.keywords = [word for (word, token) in tagged if token in tokens]

    def get_keywords(self):
        """
            Return the keywords of the sentence
            Output:
                keywords: set
        """
        return set(self.keywords)

    # GENERATE
    def get_dictionary(self):
        """
            Generates the dictionary for a sentence
            Output:
                type: dict
        """
        D = {'Language': self.language[0],
             'Type':     self.type[0],
             'Level':    self.level,
             'Keywords': self.keywords
             }
        return D

    def __str__(self):
        return self.string


# Handle input
if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Standard
        O = Conversation(input("You: "))
    else:
        O = Conversation(sys.argv[1])
    print(O)
