#!/usr/bin/python3
#
# File: main_algorithm.py
# The main algorithm that the chatbot follows.
# Note that it's technically recursive, but only returns True on its way back
# up.
# The process flowchart is a great help in understanding this structure.
#
# Copyright 2018
# The Gerrit Group
#
# Usage
# Because of socketio, can only be run with the run.py file.

# Import files
from conversation import Conversation, Sentence
from chatbot import Chatbot
from intelligent_unit import IU

# Import module
import sys

class Main:
    def __init__(self, socketio, session):
        """
        Input
            socketio - Flask SocketIO object
            session - request ID
        """
        self.cb = Chatbot(socketio, session)
        self.socket = socketio
        self.session = session
        self.iu = None
        self.conv = None
        self.already_running = False

    def run(self):
        """
        Starts up the chatbot with SocketIO and begins the execution of the main
        algorithm. Also greets the user.

        Output
            True - if the algorithm's execution finished correctly
            False - if a new session can't be started
        """
        if self.already_running:
            return False
        self.already_running = True
        self.cb.greet()
        main_complete = self.continue_at_input()
        if not main_complete:
            raise RuntimeError("Error in logical structure: "\
            "continue_at_input should always return True.")
        return main_complete

    def continue_at_input(self, old_conv=False, old_iu=False):
        """
        Continues the chatbot at the "input" phase. (see process flowchart)

        Input
            old_conv - If True, old Conversation object is kept. If not set, a
                new one's started.
            old_iu - if True, old IU object is kept. If not set, a new IU is
                initialized.
        """
        answer = self.cb.user_input()
        if not old_iu:
            self.iu = IU()
        if not old_conv:
            self.conv = Conversation(answer)
        else:
            # If this is a rephrase, add it to the conversation as well
            self.conv.add_rephrase(answer)
        self.cb.set_language(self.conv.get_main_language())
        # Continue to the chatter phase.
        if self.continue_at_chatter():
            return True
        raise RuntimeError("Error in logical structure, new input should be "\
        "followed by checking chat database.")

    def continue_at_chatter(self):
        """
        Continues the chatbot at the "match chat DB" phase, and moves through
        checking the FAQ and sending to the backend. (see process flowchart)
        """
        # Chatter phase
        self.chatter()
        # FAQ phase
        if self.check_faq():
            if self.end_conversation():
                return True
        # Backend phase
        self.call_database()
        # Then continue at viability check
        if self.continue_at_viability_check():
            return True
        raise RuntimeError("Error in logical structure, backend check should "\
        "always move on to viability check.")

    def continue_at_viability_check(self, back=False):
        """
        Continues the chatbot at the "viabililty check" phase (see proces flowchart)

        Input
            back - if this is set to True, we're entering this phase from the level
                confirm or the keywords confirm phase. If something changed there,
                and it doesn't lead to a winning URL here, we need to go back to
                the chatter step to match the new info with the FAQ and, if that
                doesn't match, to the backend.
        """
        url, answer = self.iu.get_winner()
        if url is not None:
            self.cb.link_and_answer(url, answer)
            if self.end_conversation():
                return True
            self.iu.remove_url(url)
        elif back:
            if self.continue_at_chatter():
                return True
        if self.continue_at_iu_choice():
            return True
        raise RuntimeError("Error in logical structure, failed viability check "\
        "should always move on to the IU choice.")

    def continue_at_iu_choice(self):
        """
        Continues the chatbot at the IU choice step (see proces flowchart).
        Depending on the IU's choice, one of five different courses of action
        can be taken:
            1 - confirm level
            2 - confirm keyword
            3 - extend keyword
            4 - rephrase
            5 - other measures
        """
        (action, keyword) = self.iu.choice(self.conv.get_conversation_keywords())
        if action == 1:
            # TODO: check is just here to make sure IU gets implemented correctly
            # Can probably be taken away once it works (or not, it's important)
            if self.iu.get_confirmed_level() is not None:
                raise ValueError("NOTE TO DEV: IU shouldn't choose confirm level "\
                "once it's already confirmed!")
            if self.check_level():
                return True
            if self.continue_at_iu_choice():
                return True
        elif action == 2:
            # TODO same
            if self.iu.keyword_done(keyword):
                raise ValueError("NOTE TO DEV: IU shouldn't choose a confirmed"\
                " keyword!")
            if self.check_keyword(keyword):
                return True
            if self.continue_at_chatter():
                return True
        elif action == 3:
            if self.add_keyword():
                return True
        elif action == 4:
            self.cb.rephrase()
            if self.continue_at_input(old_conv=True, old_iu=True):
                return True
        elif action == 5:
            return self.desperate_measures()
        raise RuntimeError("Error in logical structure, one of the UI outcomes or "\
        "the UI choice itself is misbehaving.")

    def chatter(self):
        """
        Chatter [noun]: purposeless or foolish talk

        This function checks if an answer can be found in the basic chat database,
        and outputs said answer. It then continues the conversation from the input
        phase.

        Uses:
            self.cb - Chatbot object for user interaction
            self.conv - Conversation object for tracking the conversation

        Output
            False if no chat match was found, True when finishing up the program
            recursively.
        """
        if self.cb.get_last_input() != self.conv.get_last_sentence().get_string():
            return False
        add = self.cb.match_additional(self.conv.get_conversation_keywords(), self.conv.get_last_sentence().get_string())
        if add is None:
            add = self.cb.match_additional(self.conv.get_last_sentence().get_keywords(), self.conv.get_last_sentence().get_string())
        if add is not None:
            self.cb.answer(add)
            sentence = self.conv.get_last_sentence()
            self.conv.remove_conversation_keywords(sentence)
            if self.continue_at_input(old_conv=True, old_iu=True):
                return True
        return False

    def check_faq(self):
        """
        Checks the FAQ database and interacts with the user for confirmation.

        Uses
            self.cb - Chatbot object for matching and user interaction
            self.conv - Conversation object to get the keywords from

        Output
            True if the right answer was found
            False if no answer or a wrong answer was found
        """
        faq = self.cb.match_faq(self.conv.get_conversation_keywords())
        if faq is not None:
            self.cb.confirm(faq[0])
            answer = self.cb.user_input()
            if self.cb.is_confirmation(answer):
                self.cb.answer(faq[1])
                return True
        return False

    def call_database(self):
        """
        Calls the backend using the agreed dictionary, and stores the gained list
        of dictionaries corresponding to URLs.

        Uses
            self.cb - Chatbot object for calling the backend
            self.conv - Conversation object for getting the input to the backend
            self.iu - IU object for storing the output
        """
        server_dict = self.conv.get_server_dictionary()
        output_dicts = self.cb.call_server(server_dict)
        print("output scores and links:")
        for o_dict in output_dicts:
            print(o_dict["Score"])
            print(o_dict["URL"])
        if not isinstance(output_dicts, list):
            raise ValueError("Backend output must be a list!")
        for output_dict in output_dicts:
            if not isinstance(output_dict, dict):
                raise ValueError("Backend list can only contain dictionaries!")
        self.iu.add_to_udl(output_dicts)

    def check_level(self):
        """
        Sets the level of the conversation based on user interaction.
        There are two possible outcomes:
        1. Nothing changes, the function above this can continue
        2. The level changes, now we need to check if there's a winning link

        Uses
            self.cb - Chatbot object for user interaction
            self.conv - Conversation object for setting the level
            self.iu - IU object for removing wrong URLs
        """
        level = self.conv.get_level()
        if level is not None:
            self.cb.confirm(level)
            answer = self.cb.user_input()
            if self.cb.is_confirmation(answer):
                self.iu.level_change(level)
                # Option 1
                return False
        answer = self.level_confirm('s')
        if self.cb.is_confirmation(answer):
            self.level_info('s')
        else:
            answer = self.level_confirm('f')
            if self.cb.is_confirmation(answer):
                self.level_info('f')
            else:
                self.conv.set_level("UvA")
                self.iu.level_change("UvA")
        # Option 2
        if self.continue_at_viability_check(back=True):
            return True
        raise RuntimeError("Error in logical structure: "\
        "continue_at_viabicursor: pointer;lity_check did not return True.")


    def level_confirm(self, level):
        """
        Asks for confirmation of the type of level from the user.

        Input:
            level - character representing the level
        Uses:
             self.cb - chatbot object for user interaction
        Output:
            the user's response (string)
        """
        if self.cb.get_language()[0] == 0:
            if level == 's':
                self.cb.confirm("een bepaalde studie")
            elif level == 'f':
                self.cb.confirm("een bepaalde faculteit")
        elif self.cb.get_language()[0] == 1:
            if level == 's':
                self.cb.confirm("a specific study program")
            elif level == 'f':
                self.cb.confirm("a specific faculty")
        # You can add responses for more languages here
        return self.cb.user_input()

    def level_info(self, level):
        """
        Specifically asks the user for the study/faculty and stores this.
        Repeat if unclear.

        Uses:
            self.cb - Chatbot object for user interaction
            self.conv - Cnversation object for saving the level
            self.iu - IU object so that URLs with wrong levels can be removed
        Input:
            level - character representing the level
        """
        if level == 's':
            if self.cb.get_language()[0] == 0:
                self.cb.level("studie")
            elif self.cb.get_language()[0] == 1:
                self.cb.level("study program")
        elif level == 'f':
            if self.cb.get_language()[0] == 0:
                self.cb.level("faculteit")
            elif self.cb.get_language()[0] == 1:
                self.cb.level("faculty")
        study = self.cb.user_input()
        temp_sentence = Sentence(study, self.conv)
        new_level = temp_sentence.get_level()
        if new_level is not None:
            self.conv.set_level(new_level)
            self.iu.level_change(new_level)
        else:
            self.cb.repeat()
            self.level_info(level)

    def check_keyword(self, keyword):
        """
        Asks the user if the keyword has to do with their query. If so, it gets
        confirmed in the IU class and this function returns False, if not, it gets
        removed from the conversation, and the algorithm continues at the viability
        check with back=True (see explanation there).

        Input:
            keyword - string, the keyword in question
        Uses:
            self.cb - Chatbot object for user interaction
            self.conv - Conversation object for keeping track of keywords
            self.iu - IU object for keeping track of confirmed keywords
        """
        self.cb.confirm(keyword)
        answer = self.cb.user_input()
        if self.cb.is_confirmation(answer):
            self.iu.keyword_change(keyword)
            return False
        self.iu.keyword_change(keyword, remove=True)
        self.conv.remove_conversation_keywords(keyword)
        if self.continue_at_viability_check(back=True):
            return True
        raise RuntimeError("Error in logical structure: "\
        "continue_at_viability_check did not return True.")

    def add_keyword(self):
        """
        Asks the user for a keyword and stores this. If it's new information, moves
        back to the chatter phase to do another FAQ check and database call,
        otherwise goes back to the IU phase.

        Uses:
            self.cb - Chatbot object for user interaction
            self.conv - Conversation object for getting and storing keywords
            self.iu - IU object to keep track of confirmed keywords
        """
        self.cb.user_keyword()
        keyword = self.cb.user_input().lower()
        if ' ' in keyword:
            self.cb.wrong_keyword()
            self.add_keyword()
        self.iu.keyword_change(keyword)
        if keyword in self.conv.get_conversation_keywords():
            if self.continue_at_iu_choice():
                return True
        self.conv.set_conversation_keywords(keyword)
        if self.continue_at_chatter():
            return True
        raise RuntimeError("Error in logical structure: "\
        "continue_at_chatter did not return True.")

    def desperate_measures(self):
        """
        Desperate measures, for if a right answer can't be found by the other
        functions. Feel free to change this to your own ideas for extra
        measures, or add more.
        """
        print("Getting desperate now.")
        # Let's try all the links that don't contain wrong levels or keywords.
        bestish_URL, bestish_answer = self.iu.get_winner(highest=True)
        if bestish_URL is not None:
            self.cb.link_and_answer(bestish_URL, bestish_answer)
            if self.end_conversation():
                return True
            self.iu.remove_url(bestish_URL)
        # As a last effort, let's ask every link from the backend that wasn't
        # asked yet.
        server_dict = self.conv.get_server_dictionary()
        output_dicts = self.cb.call_server(server_dict)
        for a_dict in output_dicts:
            poss_url = a_dict["URL"]
            poss_answer = a_dict["Answer"]
            if poss_url not in self.iu.get_wrong_urls():
                self.cb.link_and_answer(poss_url, poss_answer)
                if self.end_conversation():
                    return True
                self.iu.remove_url(poss_url)
        # If even that fails, ask for a rephrase, but now clear the conversation
        # and iu. 
        self.cb.rephrase()
        if self.continue_at_input():
            return True

    def end_conversation(self):
        """
        Asks the user if the conversation's over.
        There are three possible outcomes:
            - Conversation's over, program ends. (by returning True)
            - New conversation (i.e. with new question) is started
            - Returns False, so that the conversation can continue where it left off

        Uses
            self.cb - Chatbot object for user interaction
        """
        self.cb.confirm()
        answer = self.cb.user_input()
        if not self.cb.is_confirmation(answer):
            return False
        self.cb.finish()
        answer = self.cb.user_input()
        answer_confirm = self.cb.is_confirmation(answer)
        if answer_confirm is None:
            if self.continue_at_input():
                return True
        elif answer_confirm:
            self.cb.new_question()
            if self.continue_at_input():
                return True
        self.cb.bye()
        return True

    # Some get functions in case you need them

    def get_chatbot(self):
        return self.cb

    def get_conversation(self):
        return self.conv

    def get_iu(self):
        return self.iu

    def get_session(self):
        return self.session
