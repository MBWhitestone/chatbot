# In this file the client can set different parameters to have the chatbot work
# in a different way.

# URLs with scores under this threshhold are never chosen. (Except in the "other
# measures" step)
# [float between 0 and 1]
SCORE_THRESH = 0.5

# Under this percentage of the highest URL score, the intelligent unit will not
# take URLs into account.
# [float between 0 and 1]
SCORE_PERC = 0.75

# The "confirm keywords" step will not be repeated more often than this
# number, until the "other measures" step is taken.
# [int greater than 0]
REP_CONFIRM = 1

# The "extend keywords" step will never be repeated more often than this number
# in the conversation.
# [int greater than 0]
REP_EXTEND = 1

# Threshold before accepting an FAQ
FAQ_THRES = 0.6

# # TODO:
# Amount of max faq matches
FAQ_MATCHES = 1


# TODO
# Set the initial name of the Chatbot
NAME = "Gerrit"

# TODO
# Set the initial language of the Chatbot
# Options: "English" / "Dutch"
LANGUAGE = "English"

# Addtional matching words to ignore in input as keywords
# Used in chatbot -> match_additional
EXTRA_ADDITIONAL = ['gerrit', 'i', 'ik', 'you', 'jij', 'mijn', 'my', 'want']

# Threshold for matching the studies and faculties with input
STUDY_THRESH = 0.5
BIGRAM_FACTOR = 0.5
BIGRAM_THRESH = STUDY_THRESH*BIGRAM_FACTOR+1-BIGRAM_FACTOR
NAIVE_THRESH = 0.85
