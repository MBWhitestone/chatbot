#!/usr/bin/python3
#
# File: conversation.py
# The main class for a chatbot conversation
# Copyright 2018
# The Gerrit Group
#

# (Test) usage
# ~ python3 chatbot.py

# Imports
import random
import nltk
from ruamel.yaml import YAML
from flask_socketio import SocketIO
from threading import Thread, Event
from flask import escape, request
import time
import pwd
import os
import regex as re
from config import *

# FAQ
import search_faq
import search_extract
import chatbot_interface


class Chatbot:
    """
        The main Chatbot class
    """

    def __init__(self, socket, session, lang=(1, "English"), self_extract="extract_site/",
                 core_nl="core_nl.yml", core_en="core_en.yml",
                 add_nl="additional_nl.yml", add_en="additional_en.yml",
                 n=0, log=True):
        """
            Initialise a chatbot
        """
        self.core_nl = core_nl
        self.core_en = core_en
        self.add_en = add_en
        self.add_nl = add_nl
        self.core = None
        self.additional = None
        self.socket = socket
        self.session_id = session
        self.current = None
        self.Event = None
        self.log = log
        self.fooled = False
        self.extract = self_extract
        self.faqs = []
        self.set_language(lang)
        print(self.session_id, "Joined", self.session_id)
        socket.server.enter_room(room=self.session_id, sid=self.session_id)

        if log:

            filefound = False

            # Get Dir
            user = pwd.getpwuid(os.getuid())[0]
            directory = "logs/"+user
            if not os.path.isdir(directory):
                # os.chmod("logs", 0o777)
                # os.makedirs(directory)
                os.system("mkdir "+directory)

            # Make file
            while not filefound:
                file = directory+'/'+'conversation_'+user+'_'+ \
                       time.strftime("%d_%m_%Y")+'_'+str(n)+'.txt'
                if not os.path.isfile(file):
                    filefound = True
                else:
                    n += 1

            self.file = file
            with open(self.file, 'w') as f:
                f.write('# Conversation '+str(n)+'\n')
                f.write(time.strftime("%d-%m-%Y")+' ' +
                        time.strftime("%H:%M:%S")+'\n')
                f.write('Language: '+self.get_language()[1]+'\n')
                f.write('\n')
        # self.socket.emit('response_gerrit

    def fool(self):
        self.fooled = True

    def check_log(self, minlines=5):
        if self.log:
            remove = True
            count = 0
            for line in open(self.file, 'r'):
                count += 1
                if count > minlines:
                    remove = False
                    break

            print("count", count, "remove:", remove)
            if remove:
                os.remove(self.file)

    def user_set_language(self, num):
        """
            Change bot's language
        """
        if num == 1:
            self.socket.emit('response_gerrit', "I will talk English to you from now on", room=self.session_id, broadcast=False)
            self.set_language((num, 'English'))
        else:
            self.socket.emit('response_gerrit', "Geen mooiere taal dan het Nederlands, toch?", room=self.session_id, broadcast=False)
            self.set_language((num, 'Dutch'))

    # Language dependent settings
    def set_language(self, l: tuple):
        """
            Sets the language and the corresponding core
        """
        self.language = l
        yaml = YAML()
        if l[0] == 0:
            with open(self.core_nl) as y:
                self.core = yaml.load(y)
            with open(self.add_nl) as y:
                self.additional = yaml.load(y)
            self.faq = self.extract + "export_faq_nl.txt"
        else:
            with open(self.core_en) as y:
                self.core = yaml.load(y)
            with open(self.add_en) as y:
                self.additional = yaml.load(y)
            self.faq = self.extract + "export_faq_en.txt"
        self.socket.emit('change_language_self', l[0])

    def get_language(self):
        """
            Returns the current chatbot language
            output:
                language: tuple
        """
        return self.language

    def call_server(self, front_dict):
        """
            Call server (UvA ICT 1)
            Input:
                front_dict: dict
            Output:
                response: list (of dicts)
        """
        self.__out__(self.__call_core__('g_server'))

        # NOTE FOR FUTURE USE:
        # The backend doesn't use the keywords, so they're appended to the
        # source sentence, which is actually used.
        # If the backend is implemented in such a way that it does use the key-
        # words, this is unnecessary.
        for keyword in front_dict["Keywords"]:
            front_dict["Source"] += ' ' + keyword

        response = chatbot_interface.frontend_backend_interface(front_dict)
        temp_list = []
        for response_dict in response:
            for level in response_dict["Level"]:
                new_dict = response_dict.copy()
                new_dict["Level"] = level
                temp_list.append(new_dict)
        response = sorted(temp_list, key=lambda k: k['Score'], reverse=True)
        # response =  search_extract.backend_end_alternative(front_dict)
        if response == None:
            self.__out__(self.__call_core__('g_server_down'))
            return []
        return response

    # Answer types
    def answer(self, answer):
        """
            Anwer client
            Answer something to the user
            Input:
                answer: str
        """
        self.__out__(str(answer))

    def link_and_answer(self, url, answer):
        """
            Answer client with a link (and ask for confirmation)
            Input:
                url: str
        """
        self.__out__(self.__call_core__('g_answer'))
        self.__out__('<i><p>' + answer + '</p></i>')
        link = '<a href="' + str(url) + '" target="_blank">link</a>'
        subject = '<b>'+url.split('/')[-1].split('.')[0].replace("-"," ")+'</b>'
        self.__out__(self.__call_core__('g_link').format(link=link, subject=subject))

    def user_set_language(self):
        """
            Explain language change to user
        """
        self.__out__(self.__call_core__('g_language'))

    def confirm(self, c=None):
        """
            Ask user for confirmation
            Input:
                c: str
        """
        if c == None:
            self.__out__(self.__call_core__('g_confirmation'))
        else:
            if '?' in c:
                self.__out__(self.__call_core__(
                    'g_confirmation_question').format(faq=c))
            else:
                self.__out__(self.__call_core__(
                    'g_confirmation_addition').format(ca=c))

    def finish(self):
        """
            Ask the user if they have another question
        """
        self.__out__(self.__call_core__('g_finish'))

    def repeat(self):
        """
        Ask the user to repeat themselves.
        """
        self.__out__(self.__call_core__('g_repeat'))

    def level(self, level):
        """
            ask for a level
            Input:
                level: str
        """
        self.__out__(self.__call_core__('g_level').format(level=level))

    def user_keyword(self):
        """
            Ask the user for a keyword.
        """
        self.__out__(self.__call_core__('g_keyword'))

    def wrong_keyword(self):
        """
            Ask the user for a keyword.
        """
        self.__out__(self.__call_core__('g_wrong_keyword'))

    def rephrase(self):
        """
            Asks the user to rephrase the question.
        """
        self.__out__(self.__call_core__('g_rephrase'))

    def new_question(self):
        """
            Asks the user for his new question.
        """
        self.__out__(self.__call_core__('g_new_question'))

    def greet(self):
        """
            Greet a user
        """
        self.__out__(self.__call_core__('g_greeting'))

    def bye(self):
        """
            End a conversation
        """
        self.__out__(self.__call_core__('g_closing'))

    # Input types
    def user_input(self):
        """
            Returns input from the user
            Output:
                user_input: str
        """
        return self.__in__()

    def is_confirmation(self, str: str):
        """
            Check whether a string is a g_confirmation
            Input:
                str: str
            Returns:
                bool: True: conf, False: neg, else None
        """
        conf, neg = False, False

        for x in self.core['u_confirmation']:
            if x.lower() in str.lower():
                conf =  True

        for x in self.core['u_negation']:
            if x.lower() in str.lower():
                neg = True

        if conf and neg:
            self.__out__(self.__call_core__('g_fool'))
        elif conf:
            return conf
        elif neg:
            return not neg
        return None

    def match_faq(self, keywords: set):
        """
            Match set of keywords with FAQ
            Input:
                keywords: set
            Output:
                faq answer: tuple or None
        """
        if len(keywords) >= 2:
            faq = search_faq.get_faq(
                keywords, self.faq, self.language[1], self.faqs)
            if faq != None:
                self.faqs += [faq[0]]
            return faq
        return None

    def match_additional(self, keywords: set, sentence: str):
        """
            Match set of keywords with additional questions
            Input:
                keywords: set
            Output:
                faq answer: tuple or None
        """

        sent = [x for x in nltk.word_tokenize(sentence.lower()) if x.isalpha()]

        # Baseline using str
        for x in self.additional['conversations']:
            s = [x.lower() for x in nltk.word_tokenize(x[0]) if x.isalpha()]
            if s == sent:
                return x[1]

        l = len(keywords)
        if l:
            if (keywords - {NAME.lower()}) <= {'time', 'tijd', 'laat', 'late', 'how'}:
                return time.strftime("%H:%M:%S")

            if (keywords - {NAME.lower()}) <= {'date', 'datum', 'day', 'dag', 'vandaag', 'today', 'what', 'welke'}:
                return time.strftime("%A %d-%m-%Y")

            for x in self.additional['conversations']:
                s = [x.lower() for x in nltk.word_tokenize(x[0]) if x.isalpha()]
                # Harder to match small sentences
                if l == 1 and len(s) > 5:
                    if keywords == set(s) or keywords == set(s + EXTRA_ADDITIONAL):
                        return x[1]
                else:
                    if keywords <= set(s + EXTRA_ADDITIONAL):
                        return x[1]
        return None

    # Private class functions
    def __call_core__(self, cat: str):
        """
            Returns a random item from the category from the core
            __out__put:
                random choice: str
        """
        return random.choice(self.core[cat])

    # These functions should be modified according to the in/out destination
    def __out__(self, output):
        """
            Print output to the user
            Input:
                output: str
        """
        print("Gerrit: "+output)
        if self.log:
            with open(self.file, 'a') as f:
                f.write('C: '+output+'\n')

        print("emit at", self.session_id)
        self.socket.emit('response_gerrit', output, room=self.session_id)

    def get_last_input(self):
        return self.current

    def get_input(self, original_data):
        """
            Get async input from the user
            Input:
                original_data: str (sanitized by jQuery)
        """
        # Sanitize
        original_data = original_data['message']
        dd = original_data
        print(dd)
        original_data=re.sub("\'|\"|&|´|`", " ", original_data).strip()
        data = escape(re.sub("<.*?>|;*&lt;*|;*&gt;*|/",
                             " ", original_data)).strip()
        print('Got input!', str(data))
        self.current = str(data)

        # Log
        if self.log:
            with open(self.file, 'a') as f:
                f.write('U: '+self.current+'\n')

        # Respond
        print("emit at", self.session_id)
        self.socket.emit('my_response', dd, room=self.session_id)

        # Fool
        if len(data) != len(original_data) or self.fooled:
            self.__out__(self.__call_core__('g_fool'))
            self.fooled = False
        self.Event.set()

    def __in__(self):
        """
            Ask input from the user
            Output:
                response: str
        """
        self.Event = Event()
        while not self.Event.isSet():
            time.sleep(1)

        return self.current


# Simple test
if __name__ == "__main__":
    C = Chatbot(lang=(0, "Dutch"))
    C.greet()
    b = False
    while not b:
        C.level("studie")
        C.user_input()
        C.confirm("KI")
        C.user_input()
        C.link("https://blabla.com")
        C.confirm()
        res = C.match_faq({"Kunstmatige", "Intelligentie", ""})
        C.answer(str(res))
        a = C.user_input()
        b = C.is_confirmation(a)
    C.bye()
