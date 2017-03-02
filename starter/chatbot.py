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
from movielens import titles
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


class State:
  NEED_INFO = 0
  GENERATED_RECS = 1

"""                                    **** TODO *****


rubric: https://docs.google.com/spreadsheets/d/1_2Gkaj1eonFr16LXpeAgOdcgH2_uLTmvyCV3lQZFYEI/edit#gid=1926203681

** Unclaimed **
support user explicitly asking for a recommendation -- "Can you give me a recommendation?"
make sure rudolfa can handle multiple titles in almost any case
  ex: expand removeTitleWords function to handle multiple titles
  ex: if only some of the movies can't be matched, don't reprompt for all the movies
if bot doesn't recognize title, rubric says "use fake title"...? wtf is this

** CS **

  (1) refine recommendations
        -- clarify user-based approach
        -- item-based collaborative filtering
  (2) randomize request/confirm strings
        confirmation strings should indicate like/dislike. ex: I liked ____ too! tell me about another movie. OR  glad you enjoyed ___. Anotha one.
          -- sometimes more emotional than others depending on how much user liked it
          -- strategy: define a bunch of lists of strings that can be formatted. See reactToMovies() superPositivePhrases as an example
          -- refactor to build response instead of printing reactions. this means using += with response and not overwriting it later
  (3) identify/respond to 2 emotions
  (4) respond to arbitrary input
        -- add to faultyInput() method
        -- careful not to include emotion, asking for rec, or giving movie (w or w/o quotes) as arbitrary input because those require specific responses


  ** DONE **
    handle negation and conjunctions
    pending movies -- doesn't let user move on if there are unresolved movies.. unsure about this design but it's what we got
    refine recommendations if user wants to add more after receiving initial ones
    identifies movies without quotations using single longest substring technique
    distininguishes positive inputs from highly positive inputs and same for negative -- bot gives stronger confirmation response


** TJ **
    if movie is not in quotes, seek confirmation from user
      -- good idea. also enclose title in quotations in the original input before passing to updateSentimentDict so that removeTitleWords will work
    disambiguation by year, # in series (roman, normal, and arabic numerals), etc. see rubric
    PROBLEMS:
        if ambiguous title entered, all matches added to sentiment dict
            #Example "fast and the furious" matches two movies and thus both are entered into sentiment dict incorrectly


"""


class Chatbot:
    """Simple class to implement the chatbot for PA 6."""

    global DEBUG, yes, no, negationWords, contrastConjunctions, personalOpinionWords, superWords, containsIntensifier, MIN_REQUEST_THRESHOLD, intensifierWords, \
      superPositivePhrases

    DEBUG = True
    yes = ['yes', 'ye', 'y', 'sure']
    no = ['no', 'n', 'nah']
    negationWords = ["didn't", "don't", "isn't", 'not', "neither", "hardly", "aren't", 'never']
    contrastConjunctions = ['but', 'however', 'yet']
    intensifierWords = ['very', 'really', 'extremely', 'super', 'exceptionally', 'incredibly']
    superWords = ['love', 'hate', 'favorite', 'worst', 'awful', 'fantastic', 'amazing', 'beautiful']
    personalOpinionWords = ['I', 'i']
    MIN_REQUEST_THRESHOLD = 2
    superPositivePhrases = ['I agree {} is an unbelievable movie!! \n']

    #############################################################################
    # `moviebot` is the default chatbot. Change it to your chatbot's name       #
    #############################################################################
    def __init__(self, is_turbo=False):
      self.name = 'Rudolfa'
      self.is_turbo = is_turbo
      self.mode = '(starter) '
      self.titleList = []
      self.ratings = {}
      self.titleDict = self.createTitleDict() # Movie ID to [title, genre]
      self.binarize()
      self.p = PorterStemmer()
      self.wordToSentimentDict = collections.defaultdict(lambda: 0) # built using sentiment.txt (Ex: 'hate' --> -1)
      self.buildWordToSentimentDict()
      self.userPreferencesMap = {} # movie to +/-1 , like/dislike
      self.state = State.NEED_INFO
      self.givenRecommendations = set() # list of previously given recs not to be repeated
      self.recommendations = [] # list of top 5 movie rec IDs
      self.pendingMovies = set()
      self.stemSpecialWords()
      self.shouldGenerateReq = False
      self.firstRec = True
      self.recentReviews = {}

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

    def stemSpecialWords(self):
      global personalOpinionWords, superWords, negationWords, intensifierWords
      personalOpinionWords = map(lambda word: self.p.stem(word), personalOpinionWords)
      superWords = map(lambda word: self.p.stem(word), superWords)
      intensifierWords = map(lambda word: self.p.stem(word), intensifierWords)
      negationWords = map(lambda word: self.p.stem(word), negationWords)

    def process(self, input):
        """Takes the input string from the REPL and call delegated functions
        that
        1) extract the relevant information and
        2) transform the information into a response to the user
        """
        if self.is_turbo == True:
            self.mode = '(creative) '

        extractedMovies = self.extractMovies(input)

        #TODO fix problem of multiple matches:
        #Example "fast and the furious" matches two movies and thus both are entered into sentiment dict incorrectly
        for movie in extractedMovies:
            matches = []
            for id, title in self.titleDict.iteritems():
              if self.matchesTitle(title[0], movie, substringSearch=False):
                  matches.append(title[0])
            if len(matches) > 1:
                print 'MATCHING MORE THAN ONE MOVIES. BOTH ADDED TO SENTIMENT DICT'


        if extractedMovies:
          self.updateSentimentDict(input)
          self.reactToMovies()

        pendingMovies = self.fetchPendingMovieTitlesString()
        if pendingMovies:
          response = "I couldn't quite tell how you feel about " + pendingMovies
          response += " :(  Please tell me more about these\n"
          return response

        inputtedMoviesInfo = self.returnIdsTitlesGenres(extractedMovies)
        numInputtedMovies = len(inputtedMoviesInfo)
        if numInputtedMovies == 0:
            ambiguousMatches = self.substringMatches(input)
            print "DID YOU MEAN ONE OF THESE????"
            for movie in ambiguousMatches:
                print color.BLUE + '\n\'' + movie + '\'' + color.END + '\n'


        if self.faultyInput():
          # TODO -- gracefully handle
          return '<>'

        response = ''
        if len(self.userPreferencesMap) < MIN_REQUEST_THRESHOLD:
            response = self.notEnoughData()

        else:

            self.shouldShowReq = (self.firstRec or self.affirmative(input) or extractedMovies) and self.freshRecs()
            if self.shouldShowReq:
                # display good recommendation. Prompt for another movie rating or another recommendation
                self.popRecommendation()
                response += 'Would you like another movie recommendation? Optionally, tell me about another movie!\n'
                self.shouldShowReq = False
                self.firstRec = False
            else:
                if self.negative(input):
                  return "Guess we're done here. Enter \':quit\' to exit!"
                # couldn't get good recommendation -- ask for more
                response = self.promptUserPreRec(input)

        return response


    # TODO
    def faultyInput(self):
      return False


    # confirm that movie was received and implicitly or explicitly convey sentiment
    # bonus: reacts stronger to movies that the user really liked
    def reactToMovies(self):
      phrases = []
      for title, sentiment in self.recentReviews.iteritems():
        title = '"' + re.sub(r'\s\([0-9]*\)', '', title) + '"'
        if sentiment == -2:
          phrase = 'Damn, sorry to hear how much you hated {} :( \n'
        if sentiment == 2:
          phrase = superPositivePhrases[randint(0, len(superPositivePhrases)-1)]
        if sentiment == 1:
          phrase = 'Glad you enjoyed {}. '
        if sentiment == -1:
          phrase = "A lot of people agree {} was kinda lame.".format(title)
        phrases += [phrase.format(title)]

      print ''.join(phrases)
      self.recentReviews = {}   # reset dictionary

    # takes any movies that have been mentioned by user w/ neutral sentiment
    # and combines them into a string of the form A, B, C, . . . , or X.
    # works for any number of pending movies
    def fetchPendingMovieTitlesString(self):
      result = [self.titleDict[ID][0] for ID in self.pendingMovies]
      if not result:
        return result
      movieString = ', '.join(result)
      if len(result) > 1:
        index =  len(movieString) - len(result[-1])
        index2 = len(result[-1])
        movieString = movieString[:index] + 'or ' + movieString[-index2:]
      return movieString

    def handleInputIssues(self, inputtedMoviesInfo) :
        if len(inputtedMoviesInfo) == 0: #user enters no movie titles in quotes
            return self.mode + 'Please tell me about a movie. Remember to use double quotes around its title.'
        if ['NOT_FOUND'] in inputtedMoviesInfo: #user enters a title not in movies.txt
            return self.mode + 'Don\'t think I know that movie. Please try telling me about a different one.'


    def notEnoughData(self) :
        request = 'Anotha one.'
        confirm = 'Dats coo. '
        if len(self.userPreferencesMap) == 0: # first movie from user
            request = 'Please tell me about a movie you liked or didn\'t like.'
            confirm = ''
        return self.mode + confirm + request


    def popRecommendation(self) :
        if not self.recommendations:
          return
        rec = self.recommendations.pop(0)
        title = self.fixDanglingArticle(self.titleDict[rec][0])
        print color.BOLD + '\nI recommend \'' + title + '\'' + color.END + '\n'
        self.givenRecommendations.add(rec)

    # slightly more robust at detecting "Yes"
    def affirmative(self, input):
      if not input:
        return False
      token = input[0].lower()
      return token in yes

    # slightly more robust at detecting "No"
    def negative(self, input):
      if not input:
        return False
      token = input[0].lower()
      return token in no

    def promptUserPreRec(self, input) :

        if self.affirmative(input) and len(self.recommendations) == 0:
          return "Sorry, that was my last recommendation! Tell me more so I can help you find good movies."

        return "Sorry, couldn't find a good recommendation. Can you tell me about more movies?"


    # Identifying movies without quotation marks or perfect capitalization -- longest substring
    # Returns list of movies entered in input
    # Only returns movies that are in movies.txt
    def extractMovies(self, input) :
        titles = re.findall(r'\"(.+?)\"', input)
        if len(titles) == 0:
            titles = self.searchNoQuotes(input)
        for title in titles:
            if self.titleMatches(title) == False:
                titles.remove(title)
        return titles

#Want to return list of possibly ambiguous matches as well
#Currently only finds substrings if title is entered in quotes
# 'fast and the furious' ->
    # Fast and the Furious, The (2001)
    # 2 Fast 2 Furious (Fast and the Furious 2, The) (2003)
    # Fast and the Furious: Tokyo Drift, The (Fast and the Furious 3, The) (2006)
    # Fast & Furious (Fast and the Furious 4, The) (2009)
    # Fast and the Furious, The (1955)
    # Fast Five (Fast and the Furious 5, The) (2011)
    # Fast & Furious 6 (Fast and the Furious 6, The) (2013)
    def substringMatches(self, input) :
        ambiguousMatches = []
        titles = re.findall(r'\"(.+?)\"', input)
        for listedTitle in self.titleList:
            for title in titles:
                if self.matchesTitle(listedTitle, title, substringSearch=True):
                    ambiguousMatches.append(listedTitle)
        return ambiguousMatches

    #Searches for the single longest substring that matches a title in the list
    def searchNoQuotes(self, input) :
        matches = []
        tokens = input.split()
        for i in range(0, len(tokens)):
            testTitle = tokens[i]
            if self.titleMatches(testTitle):
                matches.append(testTitle)
            for j in range(i + 1, len(tokens)):
                testTitle += ' ' + tokens[j]
                if self.titleMatches(testTitle):
                    matches.append(testTitle)
        if matches:
            return [max(matches, key=len)]
        return []


    def titleMatches(self, testTitle) :
        for title in self.titleList:
            if self.matchesTitle(title, testTitle, substringSearch=False):
                return True
        return False


    # parses sentiment.txt into a map from word to associated sentiment (+1 or -1)
    def buildWordToSentimentDict(self):
      for word, sentiment in csv.reader(file('data/sentiment.txt'), delimiter=',', quoting=csv.QUOTE_MINIMAL):
        self.wordToSentimentDict[self.p.stem(word)] = 1 if sentiment == 'pos' else -1

      # hardcode these cases because the training data blows for these words
      self.wordToSentimentDict['fun'] = 1
      self.wordToSentimentDict['cool'] = 1

      # amplify super words
      for word in superWords:
        if word in self.wordToSentimentDict:
          self.wordToSentimentDict[word] *= 3

    def getMultiplier(self, searchWords, segment, mult):
      for word in searchWords:
        if word in segment:
          return mult
      return 1

    def containsIntensifier(window):
      for word in window:
        if word in intensifierWords:
          return True
      return False

    # Returns +1 if input sentiment is positive, otherwise -1
    # Extension: returns 2 if super positive review, -2 if super negative review
    def classifyInputSentiment(self, input):

        # split again because sometimes user expresses contrasting opinions about same movie(s)
        result = 0
        input = self.nonTitleWords(input)
        splitInput = self.splitOnConstrastingConjunctions(input)
        window = []   # contains last couple words entered -- for applying superWord multiplier
        for segment in splitInput:
          segment = segment.split()   # keep it a list to preserve word order, not a set
          multiplier = 1
          multiplier *= self.getMultiplier(personalOpinionWords, segment, 2)  # weight 'I' more than other segments b/c indicates personal opinion
          multiplier *= self.getMultiplier(negationWords, segment, -1)       # negationWords make everything imply opposite sentiment (rough but mad decent)
          for token in segment:
            stemmed = self.p.stem(token)
            sentiment = self.wordToSentimentDict[stemmed] * multiplier

            if containsIntensifier(window):
              sentiment *= 2      # super words count double

            if len(window) == 2:
              window.pop(0)
            window.append(stemmed)

            result += sentiment

        if '!' in input:    # '!' amplifies sentiment
          result *= 2

        if DEBUG:
          print 'Split input inside classifySentiment: ', splitInput
          print 'Overall result: ', result

        if result > 6:
          return 2

        if result < -6:
          return -2

        return -1 if result <= 0 else 1    # err on side of negative review so that ellipsis shit works

    def nonTitleWords(self, input):
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
        self.titles, self.originalRatings = self.loadData()
        self.titleList = [item[0] for item in self.titles]
        titlesGenres = []
        for movie in self.titles: # Create list of movie titles
            title = movie[0]
            titlesGenres.append([title, movie[1]])
        idToTitleDict = {}
        for i, movie in enumerate(self.titles):
            idToTitleDict[i] = titlesGenres[i]
        return idToTitleDict


    # Ex. 'big short, the' --> 'The big short'
    def fixDanglingArticle(self, title):
        article = 'The '
        index = title.find(', The', 0, len(title))
        if index != -1:
            pass
        elif title.find(', A', 0, len(title)) != -1:
            index =  title.find(', A', 0, len(title))
            article = 'A '
        elif title.find(', An', 0, len(title)) != -1:
            index = title.find(', An', 0, len(title))
            article = 'An '
        else:
            return title

        length = len(title)
        partOne = title[:-(length-index)]
        partTwo = title[(index + len(article) + 1):]
        title = article + partOne + partTwo
        return title

    def splitOnConstrastingConjunctions(self, input):
      for conjunction in contrastConjunctions:
        if conjunction in input:
          return input.split(conjunction)
      return [input]

    def containsSentimentWords(self, input):
      for token in input.split():
        token = self.p.stem(token)
        if token in self.wordToSentimentDict:
          return True
      return False

    # TODO: disambiguation by year, # in series (roman, normal, and arabic numerals), etc. see rubric
    def recordSentiment(self, movies, sentiment):
      for inputTitle in movies:
        for id, title in self.titleDict.iteritems():
          if self.matchesTitle(title[0], inputTitle, substringSearch=False):

            if sentiment == 0:
              self.pendingMovies.add(id)
            else:
              if id in self.pendingMovies:      # update set of movie IDs our bot is confused about
                self.pendingMovies.remove(id)
              self.recentReviews[title[0]] = sentiment    # record -2, -1, 1, or 2 so bot can confirm classification w/ user inside reactToMovies()
              self.userPreferencesMap[id] = sentiment / abs(sentiment)

    # Classifies input as overall positive or negative and stores that in dict with movie ID
    def updateSentimentDict(self, input):
        # split on any conjunctions that suggest contrasting sentiment. only handles splitting on 1 contrast conjunction
        splitInput = [input]
        allMovies = self.extractMovies(input)
        if len(allMovies) > 1:   # don't split if user is talking about the same movie throughout
          splitInput = self.splitOnConstrastingConjunctions(input)

        # classify the segments separately
        for segment in splitInput:
          sentiment = self.classifyInputSentiment(segment) if self.containsSentimentWords(segment) else 0
          movies = self.extractMovies(segment)  # extract movies specific to this segment
          self.recordSentiment(movies, sentiment)

        if DEBUG:
          print 'Split input:', splitInput
          print 'Updated sentiment dict: ', self.userPreferencesMap


    #Returns true if the inputted title matches the title listed in movies.txt
    #Handles alternate titles
    # Examples listed titles to handle:
    # "Legend of 1900, The (a.k.a. The Legend of the Pianist on the Ocean) (Leggenda del pianista sull'oceano) (1998)"
    # "Fast & Furious 6 (Fast and the Furious 6, The) (2013)"
    # "2 Fast 2 Furious (Fast and the Furious 2, The) (2003)"
    def matchesTitle(self, listedTitle, inputTitle, substringSearch) :
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
            fixedTitle = self.fixDanglingArticle(title) + ' ' + year
            fixedTitle = fixedTitle.lower()
            inputTitle = inputTitle.lower()
            if substringSearch:

                if inputTitle in fixedTitle:
                    # if len(inputTitle) > (len(fixedTitle)*(0.4)):
                    return True

            else:
                if fixedTitle == inputTitle:
                    return True
                if fixedTitle.find('the ', 0, 6) == 0:
                    fixedTitle = fixedTitle[4:]
                if fixedTitle == inputTitle:
                    return True
                if fixedTitle[:-7] == inputTitle:
                    return True
        return False

    #Returns list of [movie IDs, title, genre|genre]
    #If movie not found, [NOT_FOUND] appended instead
    def returnIdsTitlesGenres(self, inputTitles):
        movieInfo = []
        for inputTitle in inputTitles:
            for id, info in self.titleDict.iteritems():
                if self.matchesTitle(info[0], inputTitle, substringSearch=False):
                    movieInfo.append([id, info[0], info[1]])
                    break
                if id == len(self.titleDict) - 1:
                    movieInfo.append(["NOT_FOUND"])
        return movieInfo


    #############################################################################
    # 3. Movie Recommendation helper functions                                  #
    #############################################################################


    def freshRecs(self):
        if len(self.recommendations) > 0:
          return True

        self.recommendations = self.recommend()
        if DEBUG:
          print 'Recommendations: ', self.recommendations
        return len(self.recommendations) > 0


    def binarize(self):
      """Modifies the ratings matrix to make all of the ratings binary"""
      for user, ratingMap in self.originalRatings.iteritems():
        mean = sum(ratingMap.values()) / float(len(ratingMap.values()))
        self.ratings[user] = {movie: -1 if rating - mean < 0 else 1 for movie, rating in ratingMap.iteritems()}

    def dot(self, u, v):
      """Calculates a given distance function between vectors u and v using dot product"""
      commonMovies = set(u.keys()).intersection(set(v.keys()))
      if not commonMovies:
        return 0.0
      numerator = sum(u[movie] * v[movie] for movie in commonMovies)
      stdU = sum(u[movie]**2 for movie in commonMovies)
      stdV = sum(v[movie]**2 for movie in commonMovies)
      return numerator / math.sqrt(stdU * stdV)


    def recommend(self):
      """Generates a list of movies based on the input vector u using
      collaborative filtering"""

      score = 0.0
      bestFitUser = None
      for user, ratingMap in self.ratings.iteritems():
        similarity = self.dot(self.userPreferencesMap, ratingMap)
        if similarity > score:
          score = similarity
          bestFitUser = user
        # if DEBUG:
        #   print 'user: %s \t sim: %s' % (user, similarity)

      if score <= 0:
        return []

      bestFitRatingMap = self.originalRatings[bestFitUser]
      candidateMovies = set(bestFitRatingMap.keys()).difference(set(self.userPreferencesMap.keys()))  # unseen movies
      candidateMovies = list(candidateMovies.difference(self.givenRecommendations)) # unseen & unrecommended movies
      topFive = [movieID for movieID in sorted(candidateMovies, key = lambda movieID : bestFitRatingMap[movieID], reverse=True) if self.ratings[bestFitUser][movieID] == 1][:5]

      # if DEBUG:
        # print 'Candidate movies: ', candidateMovies
        # print 'Best fit user: ', bestFitUser
        # print 'Best fit rating map: ', bestFitRatingMap
        # print 'Top five: ', topFive
        # print 'Ratings: ', self.ratings[bestFitUser]

      return topFive


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


    def loadData(self, src_filename='data/ratings.txt', delimiter='%', header=False, quoting=csv.QUOTE_MINIMAL):
      title_list = titles()
      user_id_set = set()
      with open(src_filename, 'r') as f:
          content = f.readlines()
          for line in content:
              user_id = int(line.split(delimiter)[0])
              if user_id not in user_id_set:
                  user_id_set.add(user_id)
      num_users = len(user_id_set)
      num_movies = len(title_list)

      users = collections.defaultdict(lambda: {})
      reader = csv.reader(file(src_filename), delimiter=delimiter, quoting=quoting)
      for line in reader:
        users[int(line[0])][int(line[1])] =  float(line[2])
      return title_list, users


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
