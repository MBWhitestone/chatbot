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
import json
import numpy as np
from config import *

def IDF_table(keywords_list, language):
    """
    This function converts keywords into an IDF table

    Input
        keywords_list: a list of keywords for the IDF table
        language: language of the conversation

    Output
        IDF table of keywords

    """
    table = {}
    for keywords in keywords_list:
        keywords = keywords.split(',')
        for word in keywords:
            if word in table:
                table[word] += 1
            else:
                table[word] = 1

    for word in table:
        table[word] = np.log(len(keywords_list)/table[word])

    return table

def TF_table(IDF, keywords_list, language):
    """
    This function makes a TF table from an IDF table and the keywords

    Input
        IDF: IDF table created from keywords_list
        keywords_list: a list of keywords for the IDF table
        language: language of the conversation

    Output
        TF table of keywords

    """
    TF = []
    for word in IDF:
        TF.append([])
        for keywords in keywords_list:
            keywords = keywords.split(',')
            if word in keywords:
                TF[len(TF)-1].append(1)
            else:
                TF[len(TF)-1].append(0)

    TF = np.matrix(TF)
    return TF.astype(float)

def cosine_similarity(vector1, vector2, length1):
    """
    Calculates cosine similarity between two vectors

    Input
        vector1
        vector2
        length1: length of vector1

    Output
        cosine similarity

    """
    if np.sum(vector2) != 0:
        similarity = np.dot(vector1.T, vector2)[0, 0]/(np.linalg.norm(vector2)*length1)
        return similarity
    return 0

def get_faq(keywords, file, language, asked_questions):
    """
    get the best result from the FAQ above a threshold

    Input
        keywords: keywords of sentence
        file: file in specific format where keywords can be extracted from
        language: language of the conversation
        asked_questions: already asked questions in string format

    Output
        tuple of question and answer in FAQ and the keywords from the question
        
    """
    with open(file) as f:
        datastore = json.load(f)
    f.close()
    keywords_list = list(datastore.keys())
    questions_answers = [datastore[key] for key in keywords_list]

    IDF = IDF_table(keywords_list, language)
    TF = TF_table(IDF, keywords_list, language)
    #make TF_vector for keywords
    word_appearances = []

    for word in IDF:
        if word in keywords:
            word_appearances.append(1)
        else:
            word_appearances.append(0)
    #add new vector to the existing TF_table
    TF = np.c_[TF,  word_appearances]
    #multiply TF_table by corresponding IDF values
    counter = 0
    for word in IDF:
        TF[counter] = TF[counter]*IDF[word]
        counter+=1
    #take the adjusted vector from the sentence
    vector_s = TF[:, len(keywords_list)]
    length_s = np.linalg.norm(vector_s)
    if length_s==0:
        return None
    correlation = []
    #calculate cosine similarity for two vectors
    for i in range(len(keywords_list)):
        vector_t = TF[:, i]
        correlation.append(cosine_similarity(vector_s, vector_t, length_s))
    #if correlation is above certain value print the question
    index = np.argmax(correlation)
    while(questions_answers[index][0] in asked_questions or 'not included' in questions_answers[index][0]):
        correlation[index] = 0
        index = np.argmax(correlation)
    if correlation[index]>=FAQ_THRES:
        return (questions_answers[index][0], questions_answers[index][1], keywords_list[index])
    return None
