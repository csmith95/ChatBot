#!/usr/bin/env python
# -*- coding: utf-8 -*-

# PA6, CS124, Stanford, Winter 2016
# v.1.0.2
# Original Python code by Ignacio Cases (@cases)
# Ported to Java by Raghav Gupta (@rgupta93) and Jennifer Lu (@jenylu)
######################################################################
import csv
import math
import re
import numpy as np
import sys
import collections
from movielens import ratings
from random import randint
from operator import itemgetter

class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

class Chatbot:
    """Simple class to implement the chatbot for PA 6."""

    global binarize

    #############################################################################
    # `moviebot` is the default chatbot. Change it to your chatbot's name       #
    #############################################################################
    def __init__(self, is_turbo=False):
      self.name = 'Rudolfa'
      self.is_turbo = is_turbo
      self.read_data()
      self.mean_center()
      self.p = PorterStemmer()
      self.wordToSentimentDict = collections.defaultdict(lambda: 0) # built using sentiment.txt (Ex: 'hate' --> -1)
      self.buildWordToSentimentDict()
      self.sentimentDict = {} # movie to +/-1 , like/dislike
      self.titleDict = self.createTitleDict() # Movie ID to [title, genre]
      self.state = 'generating'
      self.recommendations = [] # list of top 5 movie rec IDs

    #############################################################################
    # 1. WARM UP REPL
    #############################################################################

    def greeting(self):
      """chatbot greeting message"""
      r = randint(0,6)
      messages = {
        0 : 'Suh dude.',
        1 : 'Haiiiiiiiiii',
        2 : 'How\'s it hangin, big fellah?',
        3 : 'Howdy, partner.',
        4 : 'Hola muchacho.',
        5 : 'Whats up, fucker.',
        6 : 'Yo, niqqqqqa.'
      }
      greeting_message = messages[r] + ' I\'m ' + self.name + '! I\'m going to recommend a movie for you. First I will ask you about your taste in movies. Tell me about a movie that you have seen.'

      #############################################################################
      #                             END OF YOUR CODE                              #
      #############################################################################

      return greeting_message

    def goodbye(self):
      """chatbot goodbye message"""

      r = randint(0,4)
      messages = {
        0 : 'See ya in a while crocodile :*',
        1 : 'Catch ya later alligator ;)',
        3 : 'Adios bitchacho.',
        4 : 'Alright. Fuck off then.'
      }
      goodbye_message = messages[r]

      #############################################################################
      #                             END OF YOUR CODE                              #
      #############################################################################

      return goodbye_message

    #############################################################################
    # 2. Modules 2 and 3: extraction and transformation                         #
    #############################################################################

    def process(self, input):
        """Takes the input string from the REPL and call delegated functions
        that
        1) extract the relevant information and
        2) transform the information into a response to the user
        """
        mode = '(starter) '
        if self.is_turbo == True:
            mode = '(creative) '

        self.updateSentimentDict(input)
        inputtedMoviesInfo = [] #Returns list of [movie id, title, genre|genre]
        inputtedMoviesInfo = self.returnIdsTitlesGenres(self.extractMovies(input))
        # print inputtedMoviesInfo

        #For the purposes of testing
        # self.sentimentDict = {0: 1, 8858: -1, 3464: -1, 7477: -1, 4514: -1}
        # inputtedMoviesInfo = ['not empty']
        # print self.sentimentDict


        if len(self.sentimentDict) < 3: #user hasnt entered 5 movies yet
            request = 'Anotha one.'
            confirm = 'Dats coo. '
            if len(self.sentimentDict) == 0: #first movie from user
                request = 'Please tell me about a movie you liked or didn\'t like.'
                confirm = ''
            response = mode + confirm + request
        else:
            response = 'Would you like another movie recommendation? (yes/no)'
            if self.state == 'generating':
                self.state = 'generated'
                self.recommendations = self.recommend(self.sentimentDict)
                title = self.fixTheIssue(self.titleDict[self.recommendations[0][0]][0])
                print color.BOLD + '\nI recommend \'' + title + '\'' + color.END + '\n'
                self.recommendations.pop(0)
            else:
                if 'yes' in input:
                    if len(self.recommendations) == 0:
                        response = "Sorry, that was my last recommendation!"
                    else:
                        title = self.fixTheIssue(self.titleDict[self.recommendations[0][0]][0])
                        print color.BOLD + '\nI recommend \'' + title + '\'' + color.END + '\n'
                        self.recommendations.pop(0)
                else:
                    response = "Guess we're done here. Need to figure out how to quit!"

        if self.state == 'generating':
            #user enters no movie titles in quotes
            if len(inputtedMoviesInfo) == 0:
                response = mode + 'Please tell me about a movie. Remember to use double quotes around its title.'
            #user enters a title not in movies.txt
            if ['NOT_FOUND'] in inputtedMoviesInfo:
                response = mode + 'Don\'t think I know that movie. Please try telling me about a different one.'

        #   if self.is_turbo == True:
        #     response = 'processed %s in creative mode!!' % input
        #   else:
        #     response = 'processed %s in starter mode' % input

        return response

    # Returns list of movies entered in input
    def extractMovies(self, input) :
        return re.findall(r'\"(.+?)\"', input)

    # parses sentiment.txt into a map from word to associated sentiment (+1 or -1)
    def buildWordToSentimentDict(self):
      for word, sentiment in csv.reader(file('data/sentiment.txt'), delimiter=',', quoting=csv.QUOTE_MINIMAL):
        self.wordToSentimentDict[self.p.stem(word)] = 1 if sentiment == 'pos' else -1

    # Returns +1 if input sentiment is positive, otherwise -1
    def classifyInputSentiment(self, input):
        tokens = self.nonTitleWords(input)
        tokenSet = set(tokens.split())
        result = 0
        for token in tokenSet:
          result += self.wordToSentimentDict[self.p.stem(token)]
        return 1 if result >= 0 else -1    # assuming it's not good to classify as neutral (0), err on the side of positive review

    def nonTitleWords(self, input) :
        length = len(input)
        index = input.find('\"', 0, length)
        partOne = input[:-(length-index)]
        index = input.find('\"', index + 1, length)
        partTwo = input[index + 1:]
        nonTitleWords = partOne + partTwo
        return nonTitleWords

    #Creates map from ID to movie title as listed in movies.txt [title, genre]
    #Inlcudes titles with format: Matrix, The
    def createTitleDict(self):
        self.titles1, self.ratings = ratings()
        titlesGenres = []
        for movie in self.titles1: # Create list of movie titles
            title = movie[0]
            titlesGenres.append([title, movie[1]])
        idToTitleDict = {}
        for i, movie in enumerate(self.titles):
            idToTitleDict[i] = titlesGenres[i]
        return idToTitleDict

    # Ex. 'big short, the'
    def fixTheIssue(self, title):
        index = title.find(', The', 0, len(title))
        if index == -1:
            return title
        else:
            length = len(title)
            partOne = title[:-(length-index)]
            partTwo = title[(index + 5):]
            title = 'The ' + partOne + partTwo
        return title

    #Classifies input as overall positive or negative and stores that in dict with movie ID
    def updateSentimentDict(self, input):
        binarySentiment = self.classifyInputSentiment(input)
        for inputTitle in self.extractMovies(input):
          for id, title in self.titleDict.iteritems():
              if self.matchesTitle(title[0], inputTitle):
                  self.sentimentDict[id] = binarySentiment


    #Returns true if the inputted title matches the title listed in movies.txt
    #Handles alternate titles
    # Examples listed titles to handle:
    # "Legend of 1900, The (a.k.a. The Legend of the Pianist on the Ocean) (Leggenda del pianista sull'oceano) (1998)"
    # "Fast & Furious 6 (Fast and the Furious 6, The) (2013)"
    # "2 Fast 2 Furious (Fast and the Furious 2, The) (2003)"
    def matchesTitle(self, listedTitle, inputTitle) :
        if inputTitle == listedTitle:
            return True
        regexTitles = '(^[\w\s\',:\&¡!\*\]\[\$.-]*)(\([\w\s\',:\&¡!\*\]\[\$.-]*\)\s)?(\([\w\s\',:\&¡!\*\]\[\$.-]*\)\s)?(\([0-9]{4}\)$)?'
        alternateTitles = re.findall(regexTitles, listedTitle)
        year = alternateTitles[0][3]
        for title in alternateTitles[0][:-1]:
            title = title.strip()
            if title == '':
                continue
            if 'a.k.a. ' in title:
                index = title.find('a.k.a. ', 0, len(title))
                title = title[index + 7:]
            if title[0] == '(':
                title = title[1:]
            if title[len(title) - 1] == ')':
                title = title[:-1]
            fixedTitle = self.fixTheIssue(title) + ' ' + year
            if fixedTitle.lower() == inputTitle.lower():
                return True
            if fixedTitle.find('The ', 0, 6) == 0:
                fixedTitle = fixedTitle[4:]
            if fixedTitle.lower() == inputTitle.lower():
                return True
            if fixedTitle[:-7].lower() == inputTitle.lower():
                return True
        return False

    #Returns list of [movie IDs, title, genre|genre]
    #If movie not found, [NOT_FOUND] appended instead
    def returnIdsTitlesGenres(self, inputTitles):
        movieInfo = []
        for inputTitle in inputTitles:
            for id, info in self.titleDict.iteritems():
                if self.matchesTitle(info[0], inputTitle):
                    movieInfo.append([id, info[0], info[1]])
                    break
                if id == len(self.titleDict) - 1:
                    movieInfo.append(["NOT_FOUND"])
        return movieInfo



    #############################################################################
    # 3. Movie Recommendation helper functions                                  #
    #############################################################################

    def read_data(self):
      """Reads the ratings matrix from file"""
      # This matrix has the following shape: num_movies x num_users
      # The values stored in each row i and column j is the rating for
      # movie i by user j
      self.titles, self.ratings = ratings()
      reader = csv.reader(open('data/sentiment.txt', 'rb'))
      self.sentiment = dict(reader)

    def mean_center(self):
      for user, ratingMap in self.ratings.iteritems():
        mean = sum(ratingMap.values()) / float(len(ratingMap.values()))
        self.ratings[user] = {movie: binarize(rating, mean) for movie, rating in ratingMap.iteritems()}

    def binarize(rating, mean):
      """Modifies the ratings matrix to make all of the ratings binary"""
      result = rating - mean
      if result > 0:
        return 1
      elif result < 0:
        return -1
      return 0


    def sim(self, u, v):
      """Calculates a given distance function between vectors u and v"""
      commonMovies = set(u.keys()).intersection(set(v.keys()))
      if not commonMovies:
        return 0.0
      deviationU = sum(u[movie] for movie in commonMovies)
      deviationV = sum(v[movie] for movie in commonMovies)
      stdU = sum(u[movie]**2 for movie in commonMovies)
      stdV = sum(v[movie]**2 for movie in commonMovies)
      return (deviationU * deviationV) / math.sqrt(stdU * stdV)


    def recommend(self, u):
      """Generates a list of movies based on the input vector u using
      collaborative filtering"""

      match = None
      score = 0.0
      i = None
      for user, ratingMap in self.ratings.iteritems():
        similarity = self.sim(u, ratingMap)
        if similarity > score:
          score = similarity
          match = ratingMap
          i = user
        # print 'user: %s \t sim: %s' % (user, similarity)
      unseenMovies = set(ratingMap.keys()).difference(set(u.keys()))
      topFive = []
      for movie in unseenMovies:
          if ratingMap[movie] > 0:
              if len(topFive) < 5:
                  topFive.append((movie, ratingMap[movie]))
                  topFive = sorted(topFive, key = itemgetter(1), reverse = True)
              elif ratingMap[movie] > topFive[4][1]:
                  topFive[4] = (movie, ratingMap[movie])
                  topFive = sorted(topFive, key = itemgetter(1), reverse = True)
      return topFive

    #   return [movie for movie in unseenMovies if ratingMap[movie] > 0]


    #############################################################################
    # 4. Debug info                                                             #
    #############################################################################

    def debug(self, input):
      """Returns debug information as a string for the input string from the REPL"""
      # Pass the debug information that you may think is important for your
      # evaluators
      debug_info = 'debug info'
      return debug_info


    #############################################################################
    # 5. Write a description for your chatbot here!                             #
    #############################################################################
    def intro(self):
      return """
      Your task is to implement the chatbot as detailed in the PA6 instructions.
      Remember: in the starter mode, movie names will come in quotation marks and
      expressions of sentiment will be simple!
      Write here the description for your own chatbot!
      """


    #############################################################################
    # Auxiliary methods for the chatbot.                                        #
    #                                                                           #
    # DO NOT CHANGE THE CODE BELOW!                                             #
    #                                                                           #
    #############################################################################

    def bot_name(self):
      return self.name


#############################################################################
# PorterStemmer                                                             #
#                                                                           #
# DO NOT CHANGE THE CODE BELOW!                                             #
#                                                                           #
#############################################################################
class PorterStemmer:

    def __init__(self):
        """The main part of the stemming algorithm starts here.
        b is a buffer holding a word to be stemmed. The letters are in b[k0],
        b[k0+1] ... ending at b[k]. In fact k0 = 0 in this demo program. k is
        readjusted downwards as the stemming progresses. Zero termination is
        not in fact used in the algorithm.

        Note that only lower case sequences are stemmed. Forcing to lower case
        should be done before stem(...) is called.
        """

        self.b = ""  # buffer for word to be stemmed
        self.k = 0
        self.k0 = 0
        self.j = 0   # j is a general offset into the string

    def cons(self, i):
        """cons(i) is TRUE <=> b[i] is a consonant."""
        if self.b[i] == 'a' or self.b[i] == 'e' or self.b[i] == 'i' or self.b[i] == 'o' or self.b[i] == 'u':
            return 0
        if self.b[i] == 'y':
            if i == self.k0:
                return 1
            else:
                return (not self.cons(i - 1))
        return 1

    def m(self):
        """m() measures the number of consonant sequences between k0 and j.
        if c is a consonant sequence and v a vowel sequence, and <..>
        indicates arbitrary presence,

           <c><v>       gives 0
           <c>vc<v>     gives 1
           <c>vcvc<v>   gives 2
           <c>vcvcvc<v> gives 3
           ....
        """
        n = 0
        i = self.k0
        while 1:
            if i > self.j:
                return n
            if not self.cons(i):
                break
            i = i + 1
        i = i + 1
        while 1:
            while 1:
                if i > self.j:
                    return n
                if self.cons(i):
                    break
                i = i + 1
            i = i + 1
            n = n + 1
            while 1:
                if i > self.j:
                    return n
                if not self.cons(i):
                    break
                i = i + 1
            i = i + 1

    def vowelinstem(self):
        """vowelinstem() is TRUE <=> k0,...j contains a vowel"""
        for i in range(self.k0, self.j + 1):
            if not self.cons(i):
                return 1
        return 0

    def doublec(self, j):
        """doublec(j) is TRUE <=> j,(j-1) contain a double consonant."""
        if j < (self.k0 + 1):
            return 0
        if (self.b[j] != self.b[j-1]):
            return 0
        return self.cons(j)

    def cvc(self, i):
        """cvc(i) is TRUE <=> i-2,i-1,i has the form consonant - vowel - consonant
        and also if the second c is not w,x or y. this is used when trying to
        restore an e at the end of a short  e.g.

           cav(e), lov(e), hop(e), crim(e), but
           snow, box, tray.
        """
        if i < (self.k0 + 2) or not self.cons(i) or self.cons(i-1) or not self.cons(i-2):
            return 0
        ch = self.b[i]
        if ch == 'w' or ch == 'x' or ch == 'y':
            return 0
        return 1

    def ends(self, s):
        """ends(s) is TRUE <=> k0,...k ends with the string s."""
        length = len(s)
        if s[length - 1] != self.b[self.k]: # tiny speed-up
            return 0
        if length > (self.k - self.k0 + 1):
            return 0
        if self.b[self.k-length+1:self.k+1] != s:
            return 0
        self.j = self.k - length
        return 1

    def setto(self, s):
        """setto(s) sets (j+1),...k to the characters in the string s, readjusting k."""
        length = len(s)
        self.b = self.b[:self.j+1] + s + self.b[self.j+length+1:]
        self.k = self.j + length

    def r(self, s):
        """r(s) is used further down."""
        if self.m() > 0:
            self.setto(s)

    def step1ab(self):
        """step1ab() gets rid of plurals and -ed or -ing. e.g.

           caresses  ->  caress
           ponies    ->  poni
           ties      ->  ti
           caress    ->  caress
           cats      ->  cat

           feed      ->  feed
           agreed    ->  agree
           disabled  ->  disable

           matting   ->  mat
           mating    ->  mate
           meeting   ->  meet
           milling   ->  mill
           messing   ->  mess

           meetings  ->  meet
        """
        if self.b[self.k] == 's':
            if self.ends("sses"):
                self.k = self.k - 2
            elif self.ends("ies"):
                self.setto("i")
            elif self.b[self.k - 1] != 's':
                self.k = self.k - 1
        if self.ends("eed"):
            if self.m() > 0:
                self.k = self.k - 1
        elif (self.ends("ed") or self.ends("ing")) and self.vowelinstem():
            self.k = self.j
            if self.ends("at"):   self.setto("ate")
            elif self.ends("bl"): self.setto("ble")
            elif self.ends("iz"): self.setto("ize")
            elif self.doublec(self.k):
                self.k = self.k - 1
                ch = self.b[self.k]
                if ch == 'l' or ch == 's' or ch == 'z':
                    self.k = self.k + 1
            elif (self.m() == 1 and self.cvc(self.k)):
                self.setto("e")

    def step1c(self):
        """step1c() turns terminal y to i when there is another vowel in the stem."""
        if (self.ends("y") and self.vowelinstem()):
            self.b = self.b[:self.k] + 'i' + self.b[self.k+1:]

    def step2(self):
        """step2() maps double suffices to single ones.
        so -ization ( = -ize plus -ation) maps to -ize etc. note that the
        string before the suffix must give m() > 0.
        """
        if self.b[self.k - 1] == 'a':
            if self.ends("ational"):   self.r("ate")
            elif self.ends("tional"):  self.r("tion")
        elif self.b[self.k - 1] == 'c':
            if self.ends("enci"):      self.r("ence")
            elif self.ends("anci"):    self.r("ance")
        elif self.b[self.k - 1] == 'e':
            if self.ends("izer"):      self.r("ize")
        elif self.b[self.k - 1] == 'l':
            if self.ends("bli"):       self.r("ble") # --DEPARTURE--
            # To match the published algorithm, replace this phrase with
            #   if self.ends("abli"):      self.r("able")
            elif self.ends("alli"):    self.r("al")
            elif self.ends("entli"):   self.r("ent")
            elif self.ends("eli"):     self.r("e")
            elif self.ends("ousli"):   self.r("ous")
        elif self.b[self.k - 1] == 'o':
            if self.ends("ization"):   self.r("ize")
            elif self.ends("ation"):   self.r("ate")
            elif self.ends("ator"):    self.r("ate")
        elif self.b[self.k - 1] == 's':
            if self.ends("alism"):     self.r("al")
            elif self.ends("iveness"): self.r("ive")
            elif self.ends("fulness"): self.r("ful")
            elif self.ends("ousness"): self.r("ous")
        elif self.b[self.k - 1] == 't':
            if self.ends("aliti"):     self.r("al")
            elif self.ends("iviti"):   self.r("ive")
            elif self.ends("biliti"):  self.r("ble")
        elif self.b[self.k - 1] == 'g': # --DEPARTURE--
            if self.ends("logi"):      self.r("log")
        # To match the published algorithm, delete this phrase

    def step3(self):
        """step3() dels with -ic-, -full, -ness etc. similar strategy to step2."""
        if self.b[self.k] == 'e':
            if self.ends("icate"):     self.r("ic")
            elif self.ends("ative"):   self.r("")
            elif self.ends("alize"):   self.r("al")
        elif self.b[self.k] == 'i':
            if self.ends("iciti"):     self.r("ic")
        elif self.b[self.k] == 'l':
            if self.ends("ical"):      self.r("ic")
            elif self.ends("ful"):     self.r("")
        elif self.b[self.k] == 's':
            if self.ends("ness"):      self.r("")

    def step4(self):
        """step4() takes off -ant, -ence etc., in context <c>vcvc<v>."""
        if self.b[self.k - 1] == 'a':
            if self.ends("al"): pass
            else: return
        elif self.b[self.k - 1] == 'c':
            if self.ends("ance"): pass
            elif self.ends("ence"): pass
            else: return
        elif self.b[self.k - 1] == 'e':
            if self.ends("er"): pass
            else: return
        elif self.b[self.k - 1] == 'i':
            if self.ends("ic"): pass
            else: return
        elif self.b[self.k - 1] == 'l':
            if self.ends("able"): pass
            elif self.ends("ible"): pass
            else: return
        elif self.b[self.k - 1] == 'n':
            if self.ends("ant"): pass
            elif self.ends("ement"): pass
            elif self.ends("ment"): pass
            elif self.ends("ent"): pass
            else: return
        elif self.b[self.k - 1] == 'o':
            if self.ends("ion") and (self.b[self.j] == 's' or self.b[self.j] == 't'): pass
            elif self.ends("ou"): pass
            # takes care of -ous
            else: return
        elif self.b[self.k - 1] == 's':
            if self.ends("ism"): pass
            else: return
        elif self.b[self.k - 1] == 't':
            if self.ends("ate"): pass
            elif self.ends("iti"): pass
            else: return
        elif self.b[self.k - 1] == 'u':
            if self.ends("ous"): pass
            else: return
        elif self.b[self.k - 1] == 'v':
            if self.ends("ive"): pass
            else: return
        elif self.b[self.k - 1] == 'z':
            if self.ends("ize"): pass
            else: return
        else:
            return
        if self.m() > 1:
            self.k = self.j

    def step5(self):
        """step5() removes a final -e if m() > 1, and changes -ll to -l if
        m() > 1.
        """
        self.j = self.k
        if self.b[self.k] == 'e':
            a = self.m()
            if a > 1 or (a == 1 and not self.cvc(self.k-1)):
                self.k = self.k - 1
        if self.b[self.k] == 'l' and self.doublec(self.k) and self.m() > 1:
            self.k = self.k -1

    def stem(self, p, i=None, j=None):
        """In stem(p,i,j), p is a char pointer, and the string to be stemmed
        is from p[i] to p[j] inclusive. Typically i is zero and j is the
        offset to the last character of a string, (p[j+1] == '\0'). The
        stemmer adjusts the characters p[i] ... p[j] and returns the new
        end-point of the string, k. Stemming never increases word length, so
        i <= k <= j. To turn the stemmer into a module, declare 'stem' as
        extern, and delete the remainder of this file.
        """
        if i is None:
            i = 0
        if j is None:
            j = len(p) - 1
        # copy the parameters into statics
        self.b = p
        self.k = j
        self.k0 = i
        if self.k <= self.k0 + 1:
            return self.b # --DEPARTURE--

        # With this line, strings of length 1 or 2 don't go through the
        # stemming process, although no mention is made of this in the
        # published algorithm. Remove the line to match the published
        # algorithm.

        self.step1ab()
        self.step1c()
        self.step2()
        self.step3()
        self.step4()
        self.step5()
        return self.b[self.k0:self.k+1]

#############################################################################
# End PorterStemmer                                                         #
#                                                                           #
# DO NOT CHANGE THE CODE ABOVE!                                             #
#                                                                           #
#############################################################################

if __name__ == '__main__':
    Chatbot()
    ## PorterStemmer code below ##
    p = PorterStemmer()
    if len(sys.argv) > 1:
        for f in sys.argv[1:]:
            infile = open(f, 'r')
            while 1:
                output = ''
                word = ''
                line = infile.readline()
                if line == '':
                    break
                for c in line:
                    if c.isalpha():
                        word += c.lower()
                    else:
                        if word:
                            output += p.stem(word, 0,len(word)-1)
                            word = ''
                        output += c.lower()
                print output,
            infile.close()
