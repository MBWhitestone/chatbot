# Tweedejaarsproject 2018
## University of Amsterdam | Copyright 2018

## Authors
* Bence Tijssen
* Bram Akkerman
* Mattijs Blankesteijn
* Thomas van Osch
* Tim Ottens

## About
This repository contains data for the second year AI bachelor project course at
the UvA in June 2018. It is a project for the UvA ICT group about chatbots.

## Start
**Only first time:**
> $ sudo chmod +x run

**Normal**:
>  $ ./run

And open webrowser at [0.0.0.0:5000](http://0.0.0.0:5000)

## Configure
To change the chatbots behaviour different parameters in the config.py file in 
*/chatbot* can be changed.

## Dependencies
To run the code in this repository the following python3 libraries are needed:

- ast
- bs4 (beautifulsoup)
- collections
- datetime
- eventlet
- flask
- flask- socketio
- gevent
- json
- more- itertools
- nltk (words, stopwords, averaged_perceptron_tagger, tagset, universal_tagset, punkt, metrics, stem)
- numpy
- os
- pwd
- random
- regex
- requests
- ruamel.yaml
- setuptools
- sys
- threading
- time
- watson_developer_cloud

## Files
Sections refer to sections in the report.  
In *chatbot*:  
- **run.py** The main file to run, responsible for setting up a *server*, a *socket* and for keeping track of different *sessions*
- **main\_algorithm.py** The file with the Main class (Section 2.2.4), responsible for using the chatbot logic as described in Section 2.1
- **conversation.py** The file with the Conversation and Sentence class (Section 2.2.1), responsible for the whole conversation
- **chatbot.py** The file with the Chatbot class (Section 2.2.2), responsible for user interaction
- **intelligent\_unit.py** The file with the IU class (Section 2.2.4) responsible for choosing the next action for the chatbot
- **search\_faq.py** The script responsible for searching Frequently- Asked- Questions matching (Section 2.4.4)
- **config.py** The file with some important parameters of the chatbot
- **additional\_en.yml** The YAML database with some English questions and answers as described in Section 2.4.3
- **additional\_nl.yml** The YAML database with some Dutch questions and answers as described in Section 2.4.3
- **core\_en.yml** The YAML database with some generic English ways of sentence behaviour as described in Section 2.4.3
- **core\_nl.yml** The YAML database with some generic Dutch ways of sentence behaviour as described in Section 2.4.3
- **faq\_neural.py** A start for future matching expansion of the bot using Neural Networks (Section 4.2.3).

In *chatbot/interface*:
- **bot.html** The main HTML for the interface
- Some other image files for the user-interface

In *chatbot/extract_site*:  
Different files to handle crawling studies, faculties, faq, and abbreviations of the UvA web domain

## Specific Known Issues
This is an (incomplete) list of current issues in the chatbot

### Client-Server Unicode Handling
Something inside socket.IO is not correctly parsing unicode:
- Client log before sending: ë
- Server log input: Ã\guillemotleft
This was an issue in earlier versions of Flask-Socketio, however it is unclear why it is still a problem for the version used in this implementation.

### Study and Faculty Matching
The current implementation uses less advanced files for recognising studies and faculties due to limitations in the types the backend can give. This also implies that faculty matching is not possible with abbreviations yet.

### Chat Switching
As soon as the chatbot starts searching the UvA backend further questions bases on that are not always matched with normal small talk. This usually only happens in cases where the end-user is not seriously searching.

### Double Information
Due to double information on the UvA web domain (for example the same page on different study pages) gerrit tends to return more than one time the same page from a different study. This could be partially solved by saving the page subject, which can already be extracted, to a list of negatively confirmed subjects in order to not return them in the same conversation.

![uva-logo](chatbot/interface/uvalogo_regular_en.jpg)
