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
from movielens import titles, ratings
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
  (2) identify/respond to 2 emotions
  (3) respond to arbitrary input
        -- add to faultyInput() method
        -- careful not to include emotion, asking for rec, or giving movie (w or w/o quotes) as arbitrary input because those require specific responses


  ** DONE **
    handle negation and conjunctions
    pending movies -- doesn't let user move on if there are unresolved movies.. unsure about this design but it's what we got
    refine recommendations if user wants to add more after receiving initial ones
    searchNoQuotes identifies movies without quotations using single longest substring technique
        returns input with newly inserted quotes for title to be extracted as normal
    distininguishes positive inputs from highly positive inputs and same for negative -- bot gives stronger confirmation response
    toy story disambiguation
    (2) randomize request/confirm strings
    handles basic emotions
    "1" matches to 187
    i like "the matrix" vs i like the "matrix". --> no quotes works
    Not finding title without quotes if immediately followed by punctuation
    asks me if i want another rec and it responds to yes or no with a generalResponse


** TJ **
    disambiguation by year, # in series (roman, normal, and arabic numerals), etc. see rubric
"""


class Chatbot:
    """Simple class to implement the chatbot for PA 6."""

    global DEBUG, yes, no, negationWords, contrastConjunctions, personalOpinionWords, superWords, containsIntensifier, MIN_REQUEST_THRESHOLD, intensifierWords, \
      superPositivePhrases, superNegativePhrases, positivePhrases, negativePhrases, additionalRequests, initialRequests, greetings, goodbyes, tellMeMoreRequests, \
      anotherRecOrRefinePrompts, exitResponses, noMovieDetectedResponses, lastRecResponses, cantRecommendMovieResponses, enterNumBelowResponses, disambiguateMovieResponses, \
      angryWords, happyWords, generalReponses, movieMatchesEmpty, helloWords, fillerWords, recStrings
    DEBUG = False
    yes = ['yes', 'ye', 'y', 'sure']
    no = ['no', 'n', 'nah']
    negationWords = ["didn't", "don't", "isn't", 'not', "neither", "hardly", "aren't", 'never']
    contrastConjunctions = ['but', 'however', 'yet']
    intensifierWords = ['very', 'really', 'extremely', 'super', 'exceptionally', 'incredibly']
    superWords = ['love', 'hate', 'favorite', 'worst', 'awful', 'fantastic', 'amazing', 'beautiful']
    personalOpinionWords = ['I', 'i']
    MIN_REQUEST_THRESHOLD = 2
    angryWords = ['angry', 'anger', 'hate', 'mad', 'pissed', 'annoyed', 'bitter', 'enraged', 'furious', 'heated', 'offended', 'upset']
    happyWords = ['happy', 'joyful', 'excited', 'delight', 'delighted', 'thrilled', 'pleased', 'glad', 'jubilant', 'cheerful']
    helloWords = ['hey', 'hi', 'hello']
    movieMatchesEmpty = True


    superPositivePhrases = ['I agree {} is an unbelievable movie!! ',
                            'Yeah, {} was absolutely fantastic! ',
                            'You\'re so right. {} was definitely a great movie! ']
    superNegativePhrases = ['Damn, sorry to hear how much you hated {} :( ',
                            'Thats really too bad you didn\'t like {} :( ',
                            'Wow, yeah I can understand why you hated {}! ']
    positivePhrases = ['Glad you enjoyed {}. ',
                       'Yeah, {} was pretty good. ',
                       'I also thought {} was a good movie. ']
    negativePhrases = ['A lot of people agree {} was kinda lame. ',
                       'Yeah, {} wasn\'t great. ',
                       'Agreed. {} could have been better. ']
    additionalRequests = ['Tell me about another one. ',
                          'Can you tell me about another movie? ',
                          'MORE! Whats another movie you liked/disliked? ']
    initialRequests = ['Please tell me about a movie you liked or didn\'t like. ',
                       'Tell me about a movie you either liked or didn\'t like. ',
                       'What\'s a movie you liked or didn\'t like? ']
    fillerWords = ['Ummm ', 'Uhhh ', 'Mmmm ']
    greetings = ['Suh dude.',
                 'Heyyyyyyy.',
                 'How\'s it hangin, big fellah?',
                 'Howdy, partner.',
                 'Hola muchacho.']
    goodbyes = ['See ya in a while crocodile :*',
                'Catch ya later alligator ;)',
                'Adios muchacho.']
    tellMeMoreRequests = [' :(  Please tell me a little more.',
                          ' Do you mind telling me a little more?',
                          ' How do you feel about that movie?']
    anotherRecOrRefinePrompts = ['Would you like another movie recommendation? Optionally, tell me about another movie!',
                                 'Do you want another recommendation? You can also tell me about another movie.',
                                 'Should I give you another recommendation? If you want, you can tell me about another movie.']
    exitResponses = ['Guess we\'re done here. Enter \':quit\' to exit!',
                     'Okay then! Enter \':quit\' to exit!',
                     'Fine, leave me then! Enter \':quit\' to exit!']
    noMovieDetectedResponses = ['Please tell me about a movie. Remember to use double quotes around its title.',
                                'Can you tell me about a movie? Please use double quotes around its title!',
                                'Tell me about a movie you like/dislike. Make sure you use double quotes around its title.']
    dontRecognizeMovieResponses = ['Don\'t think I know that movie. Please try telling me about a different one.',
                                   'Hmmm. I don\'t recognize that movie. Can you try telling me about a different one?',
                                   'I\'ve never heard of that movie before. Please try telling me about another movie.']
    lastRecResponses = ['Sorry, that was my last recommendation! Tell me more so I can help you find good movies.',
                        'Unforunately, that was my last recommendation. If you tell me more, I can think of other recommendations!',
                        'I\'m out of recommendations. You can tell me more if you still need more recommendations!']
    cantRecommendMovieResponses = ['Sorry, couldn\'t find a good recommendation. Can you tell me about more movies?',
                                   'I was unable to recommend a good movie! Please tell me about more movies.',
                                   'Sorry man, I can\'t offer a good recommendation. You should tell me about more movies.']
    enterNumBelowResponses = ['Sorry, please enter a number shown below',
                              'Please enter one of the numbers below (Example: \'1\')',
                              'Can you please enter one of the numbers shown below?']
    disambiguateMovieResponses = ['Wasn\'t quite sure which movie you meant. Which of the below did you mean?',
                                  'Not quite sure which movie you\'re talking about. Which of the below did you mean?',
                                  'Hey, I actually don\'t know which movie you\'re referring to. Which of the below did you mean?']
    generalReponses = ['Thats an odd thing to say. Why don\'t you use me for what I\'m designed to do and tell me about a movie.',
                       'I suspect that you have forgotten my true purpose... Maybe try not being weird and tell me about a movie.',
                       'Bro you\'re kind of cramping my style. Let\'s try this. Tell me about the last movie you saw.',
                       'I don\'t think even a human would understand how you want me to respond... movie?',
                       'Ummm thats nice. Why don\'t you tell me about a movie?',
                       'No stop it. I\'m here to recommend movies not deal with your inability to understand directions.',
                       'Stop. Take a second to think about who you\'re talking to. Thats right. A computer. Now tell me about a movie.',
                       'Yeah thats great... Seen any good movies lately?',
                       'Okay. We could do this all day. Why don\'t you just tell me about a movie.']
    recStrings = ['I bet you would dig "{}"',
                  'You should for sure watch "{}"',
                  'Sounds like you would love "{}"',
                  'Watch "{}". I\'ll be here when you come back to hear what you thought!']
    #############################################################################
    # `moviebot` is the default chatbot. Change it to your chatbot's name       #
    #############################################################################
    def __init__(self, is_turbo=False):
      self.name = 'Rudolfa'
      self.titleList = []
      self.ratings = None
      self.userPreferencesVector = [] # +/-1, index is movieID
      self.loadData()
      self.titleDict = self.createTitleDict() # Movie ID to [title, genre]
      self.binarize()
      self.p = PorterStemmer()
      self.wordToSentimentDict = collections.defaultdict(lambda: 0) # built using sentiment.txt (Ex: 'hate' --> -1)
      self.buildWordToSentimentDict()
      self.preferencesRecorded = 0
      self.state = State.NEED_INFO
      self.givenRecommendations = set() # list of previously given recs not to be repeated
      self.recommendations = [] # list of top 5 movie rec IDs
      self.pendingMovie = None
      self.stemSpecialWords()
      self.shouldGenerateReq = False
      self.firstRec = True
      self.recentReviews = collections.defaultdict(lambda: 0)
      self.movieMatches = []
      self.disambiguationInProgress = False
      self.disambiguationJustResolved = False
      self.cachedSentiment = 0   # for movie disambiguation

    #############################################################################
    # 1. WARM UP REPL
    #############################################################################

    def greeting(self):
      """chatbot greeting message"""
      greeting_message = greetings[randint(0,len(greetings)-1)] + ' I\'m ' + self.name + '! I\'m going to recommend a movie for you. First I will ask you about your taste in movies. Tell me about a movie that you have seen.'
      return greeting_message

    def goodbye(self):
      """chatbot goodbye message"""
      goodbye_message = goodbyes[randint(0,len(goodbyes)-1)]
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

    def getMatchingMovieOptions(self):
      options = color.RED
      for index, possibility in enumerate(self.candidateMovies):
          options += '\n({}) {} \n'.format(index+1, possibility[0])
      options += color.END
      return options

    def handleQuestions(self, input):
      input = input.lower()
      if input.startswith('can'):
        split = input.split()
        if 'rec' in split or 'recommendation' in split or 'recommend' in split:
          return 'GIVE_REC'
        return "Sorry, I can't help ya there. "
      if input.startswith('what') or input.startswith('how'):
        return "I'm not really sure, pal. How about these apples: "
      return ''

    def process(self, input):
        """Takes the input string from the REPL and call delegated functions
        that
        1) extract the relevant information and
        2) transform the information into a response to the user
        """

        response = ''
        # handle questions like "Can you... " or "What is..."
        response += self.handleQuestions(input)
        if response:
          if response == 'GIVE_REC':
            if self.freshRecs():
              response = 'Sure!\n'
              response += self.popRecommendation()
              return response + anotherRecOrRefinePrompts[randint(0, len(anotherRecOrRefinePrompts))-1]
            else:
              return cantRecommendMovieResponses[randint(0, len(cantRecommendMovieResponses))-1]
          return response + initialRequests[randint(0, len(initialRequests))-1]


        # if pending movie, just append it to whatever the user inputted and classify it as that
        if self.pendingMovie:
          input += ' ' + self.pendingMovie[1]
          self.pendingMovie = None

        input = self.searchNoQuotes(input) #In case no quotes used around potential title, searches for substring, adds quotes
        disambiguationResponse = self.disambiguate(input)
        if disambiguationResponse:
          return disambiguationResponse
        else:
          response += self.reactToMovies() # after resolving disambiguation, this will return reaction. if nothing resolved, will return empty

        # *** any code below here can assume disambiguation has been resolved ***

        extractedMovies = self.extractMovies(input)
        if extractedMovies:
          if extractedMovies[0] == 'NOT_FOUND':
            return 'Sorry, I don\'t recognize the movie "{}" :( Guess I\'m not as smart as I thought. '.format(extractedMovies[1])
          self.updateSentimentDict(input)
          response += self.reactToMovies()
          if self.pendingMovie:
            response += 'How did you feel about "{}"?'.format(self.fixDanglingArticle(self.pendingMovie[1]))
            return response

        if movieMatchesEmpty and not self.disambiguationJustResolved and not self.affirmative(input) and not self.negative(input):
            return self.respondFaultyInput(input)
        self.disambiguationJustResolved = False

        if self.preferencesRecorded < 5:
            response += self.notEnoughData()
        else:
            self.shouldShowReq = (self.firstRec or self.affirmative(input)) and self.freshRecs()
            if self.shouldShowReq:
                # display good recommendation. Prompt for another movie rating or another recommendation
                response += self.popRecommendation()
                response += anotherRecOrRefinePrompts[randint(0,len(anotherRecOrRefinePrompts)-1)]
                self.shouldShowReq = False
                self.firstRec = False
            else:
                if self.negative(input) and not extractedMovies:
                  return exitResponses[randint(0,len(exitResponses)-1)]
                # couldn't get good recommendation -- ask for more
                response += self.promptUserPreRec(input)
        if DEBUG:
            print 'Number of prefs recorded: ', self.preferencesRecorded
        return response


    def gaugeEmotion(self, input, emotionWords):
      window = []
      for word in input:
        if word in emotionWords:
          for prevWord in window:
            if prevWord in negationWords:
              return -1    # user is expressing opposite of emotion
          return 1 # user is expressing emotion
        if len(window) == 2:
          window.pop(0)
        window.append(word)
      return 0   # neutral

    def respondFaultyInput(self, input) :
        global angryWords, happyWords, helloWords
        input = input.lower().split()
        # first look for emotion
        happy = self.gaugeEmotion(input, happyWords)
        if happy != 0:
          if happy == 1:
            response = 'I\'m glad that you\'re happy. Since you\'re in such a good mood, '
            response += initialRequests[randint(0, len(initialRequests)-1)].lower()
            return response
          if happy == -1:
            return "I'm sorry you're not feeling too good. Let's talk about good movies to cheer ya up! "

        angry = self.gaugeEmotion(input, angryWords)
        if angry != 0:
          if angry == 1:
            response = 'I\'m sorry that you\'re angry. If it helps you calm down, '
            response += initialRequests[randint(0, len(initialRequests)-1)].lower()
            return response
          if angry == -1:
            return "Good to hear I haven't upset you. Tell me about some good movies."

        hello = self.gaugeEmotion(input, helloWords)
        if hello == 1:
          response = 'Um yeah, hello to you too. '
          response += initialRequests[randint(0, len(initialRequests)-1)].lower()
          return response

        # general response
        return generalReponses[randint(0, len(generalReponses)-1)]


    # Takes all titles in quotes and returns a dict of them to a list of their
    # possible matches. If no exact matches exist, looks for substrings
    # 1) User enters substring in quotes
    # 2) user enters full title in quotes
    # user enters full title no quotes taken care of previously
    def extractMovieMatches(self, input) :
        global movieMatchesEmpty
        movieMatches = {}
        titles = re.findall(r'\"(.+?)\"', input)
        if titles: #Cases 1, 2
            for title in titles:
                movieMatches[title] = self.returnMatches(title)
        if DEBUG:
            print movieMatches
        if movieMatches:
            movieMatchesEmpty = False
        else:
          movieMatchesEmpty = True
        return movieMatches

    #For each possible title entered, returns list of possible matches inlcuding substring matches
    # list contains (Title, ID)
    def returnMatches(self, inputTitle) :
        matches = [] #Stores list of matches for every title entered
        for id, title in enumerate(self.titleList):
          if self.matchesTitle(title, inputTitle, substringSearch=False):
            matches.append((title, id))
        if not matches: #no exact matches, looks for substring matches
          matches = self.substringMatches(inputTitle)
        return matches

    # confirm that movie was received and implicitly or explicitly convey sentiment
    # bonus: reacts stronger to movies that the user really liked
    def reactToMovies(self):
      phrases = []
      phrase = ''
      for title, sentiment in self.recentReviews.iteritems():
        title = '"' + re.sub(r'\s\([0-9]*\)', '', title) + '"'
        if sentiment == -2:
          phrase = superNegativePhrases[randint(0, len(superNegativePhrases)-1)]
        if sentiment == 2:
          phrase = superPositivePhrases[randint(0, len(superPositivePhrases)-1)]
        if sentiment == 1:
          phrase = positivePhrases[randint(0, len(positivePhrases)-1)]
        if sentiment == -1:
          phrase = negativePhrases[randint(0, len(negativePhrases)-1)]
        phrases += [phrase.format(title)]

      self.recentReviews = {}   # reset dictionary

      reaction = ''.join(phrases)
      return reaction

    def handleInputIssues(self, inputtedMoviesInfo) :
        if len(inputtedMoviesInfo) == 0: #user enters no movie titles in quotes
            return noMovieDetectedResponses[randint(0,len(noMovieDetectedResponses)-1)]
        if ['NOT_FOUND'] in inputtedMoviesInfo: #user enters a title not in movies.txt
            return dontRecognizeMovieResponses[randint(0,len(dontRecognizeMovieResponses)-1)]


    def notEnoughData(self) :
        request = additionalRequests[randint(0, len(additionalRequests)-1)]
        if len(self.userPreferencesVector) == 0: # first movie from user
            request = initialRequests[randint(0, len(initialRequests)-1)]
        return request

    def popRecommendation(self) :
        if not self.recommendations:
          return ''
        rec = self.recommendations.pop(0)
        title = self.fixDanglingArticle(self.titleDict[rec][0])
        self.givenRecommendations.add(rec)
        return color.BOLD + '\n\n' + recStrings[randint(0, len(recStrings))-1].format(title) + color.END + '\n\n'

    # slightly more robust at detecting "Yes"
    def affirmative(self, input):
      if not input:
        return False
      token = input.split()[0].lower()
      return token in yes

    # slightly more robust at detecting "No"
    def negative(self, input):
      if not input:
        return False
      token = input.split()[0].lower()
      return token in no

    def promptUserPreRec(self, input) :

        if len(self.recommendations) > 0:
          return anotherRecOrRefinePrompts[randint(0,len(anotherRecOrRefinePrompts))-1]

        return cantRecommendMovieResponses[randint(0,len(cantRecommendMovieResponses)-1)]


    # Returns list of movies entered in input
    # Only returns movies that match a title in movies.txt
    #PROBLEM: returning "matrix" when input is "matrix", but not returning "the matrix" when input is "the matrix"
    def extractMovies(self, input) :
        titles = re.findall(r'\"(.+?)\"', input)
        for title in titles:
            if self.titleMatches(title) == False:
                return ['NOT_FOUND', title]
        if DEBUG:
            print 'extractMovies() - titles entered that match movies in db: %s' % titles
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
    def substringMatches(self, inputTitle) :
        ambiguousMatches = []
        # titles = re.findall(r'\"(.+?)\"', input)
        for index, listedTitle in enumerate(self.titleList):
            # for title in titles:
            if self.matchesTitle(listedTitle, inputTitle, substringSearch=True):
                ambiguousMatches.append((listedTitle, index))
        return ambiguousMatches

    #If no titles in quotes, searches for the single longest substring that matches a title in the list
    #Returns input with newly inserted quotes around title
    def searchNoQuotes(self, input) :
        titles = re.findall(r'\"(.+?)\"', input)
        if not titles:
            matches = []
            tokens = input.split()
            for i in range(0, len(tokens)):
                testTitle = tokens[i]
                if self.titleMatches(testTitle):
                    if tokens[i-1].lower() != 'i' or i == len(tokens) - 1:
                        matches.append(testTitle)
                for j in range(i + 1, len(tokens)):
                    testTitle += ' ' + tokens[j]
                    if self.titleMatches(testTitle):
                        if tokens[i-1].lower() != 'i' or j == len(tokens) - 1:
                            matches.append(testTitle)
            if matches:
                title = max(matches, key=len)
                index = input.find(title, 0, len(input))
                input = input[:index] + '\"' + title + '\" ' + input[index + len(title) + 1:]
                if DEBUG:
                    print 'searchNoQuotes() - changed input to %s' % input
        return input


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
        input = self.nonTitleWords(input)
        splitInput = self.splitOnConstrastingConjunctions(input)
        window = []   # contains last couple words entered -- for applying superWord multiplier
        for segment in splitInput:
          result = 0
          segment = segment.split()   # keep it a list to preserve word order, not a set
          multiplier = 1
          multiplier *= self.getMultiplier(personalOpinionWords, segment, 2)  # weight 'I' more than other segments b/c indicates personal opinion
          multiplier *= self.getMultiplier(negationWords, segment, -1)       # negationWords make everything imply opposite sentiment (rough but mad decent)
          for token in segment:
            stemmed = self.p.stem(token)
            sentiment = self.wordToSentimentDict[stemmed] * multiplier
            if stemmed == 'thought':
              continue
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

        print result
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
              self.pendingMovie = (id, self.fixDanglingArticle(title[0]))
            else:
              if self.pendingMovie and id == self.pendingMovie[0]:      # update set of movie IDs our bot is confused about
                self.pendingMovie = None
              self.recentReviews[title[0]] = sentiment    # record -2, -1, 1, or 2 so bot can confirm classification w/ user inside reactToMovies()
              self.preferencesRecorded += 1 if self.userPreferencesVector[id] == 0 else 0   # increment if movie hasn't been rated by user yet
              self.userPreferencesVector[id] = sentiment / abs(sentiment)

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
          if self.disambiguationInProgress:
            self.cachedSentiment = sentiment
          else:
            self.recordSentiment(movies, sentiment)



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
                    if len(inputTitle) > (len(fixedTitle)*(0.5)):
                        if len(fixedTitle) > 10:
                            return True
            else:
                if fixedTitle == inputTitle:
                    return True
                if fixedTitle.find('the ', 0, 6) == 0:
                    if fixedTitle[4:] == inputTitle:
                        return True
                    if len(year) == 6:
                        if fixedTitle[4:-7] == inputTitle:
                            return True
                punctuation = '.,!?'
                if len(year) == 6:
                    if fixedTitle[:-7] == inputTitle:
                        return True
                    #changes
                    if inputTitle[len(inputTitle) - 1] in punctuation:
                        if fixedTitle[:-7] == inputTitle[:-1]:
                             return True
                    #
                    try:
                        num = int(fixedTitle[len(fixedTitle) - 8])
                        if fixedTitle[:-9] == inputTitle and len(fixedTitle) > 11:
                            return True
                    except:
                        continue
                else:
                    #changes
                    if inputTitle[len(inputTitle) - 1] in punctuation:
                        if fixedTitle == inputTitle[:-1]:
                             return True
                    #
                    try:
                        num = int(fixedTitle[:-1])
                        if fixedTitle[:-2] == inputTitle and len(fixedTitle) > 4:
                            return True
                    except:
                        continue
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

    def binarizeHelper(self, num):
      if num >= 2.5:
        return 1
      if num == 0:
        return 0
      return -1

    def binarize(self):
      """Modifies the ratings matrix to make all of the ratings binary"""
      binarizer = np.vectorize(self.binarizeHelper)

      self.ratings[np.where(self.ratings >= 2.5)] = -2
      self.ratings[np.where(self.ratings >= 0.5)] = -1
      self.ratings[np.where(self.ratings == -2)] = 1

    def sim(self, u, v):
      return np.dot(u, v) / (np.sqrt(np.dot(u, u)) * np.sqrt(np.dot(v, v)))


    def recommend(self):
      """Generates a list of movies based on the input vector u using
      collaborative filtering"""

      neighborMoviesMap = {id : ratings for id, ratings in enumerate(self.ratings) if self.userPreferencesVector[id] != 0}
      unratedMovies = {id : ratings for id, ratings in enumerate(self.ratings) if self.userPreferencesVector[id] == 0 and id not in self.givenRecommendations}
      extrapolatedRatings = {}
      for unratedID, ratings in unratedMovies.iteritems():
        simMap = {id : self.sim(ratings, ratingVector) for id, ratingVector in neighborMoviesMap.iteritems()}
        rating = sum(self.userPreferencesVector[id]*weight for id, weight in simMap.iteritems()) # weighted sum
        if rating > .6:
          extrapolatedRatings[unratedID] = rating

      topRatings = [id for id, rating in sorted(extrapolatedRatings.iteritems(), key=lambda x:x[1], reverse=True)][:5]
      return topRatings


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

      return "  Meet Rudolfa! Rudolfa is always runnig in creative mode and can do things like: \n\n" + \
                "\t * identify movies without quotations or capitalization\n" + \
                "\t * fine-grained sentiment extraction involving strong emotion words and intesifiers. I respond differently if you really love/hate something. Even try this with multiple movies.\n" + \
                "\t * disambiguate movie titles for series and year ambiguities\n" + \
                "\t * extract sentiment with multiple-movie input, including opposite sentiments \n" + \
                "\t * identify and respond to 2 types of emotion (angry/upset and happy/excited) \n" + \
                "\t * understand references to things said previous, like in the Titanic example on the rubric \n" + \
                "\t * respond to arbitrary input to steer the conversation back to movies\n" + \
                "\t * speak pretty fluently \n" + \
                "\t * respond to questions of the form 'Can/How/What ...'? Try asking me for a recommendation!  \n" + \
                "\t * recognize alternate titles \n\n" + \
                "  Enjoy!!\n"



    #############################################################################
    # Auxiliary methods for the chatbot.                                        #
    #                                                                           #
    # DO NOT CHANGE THE CODE BELOW!                                             #
    #                                                                           #
    #############################################################################

    def bot_name(self):
      return self.name

    def loadData(self):
      self.titles, self.ratings = ratings()
      self.userPreferencesVector = np.zeros(len(self.titles))
      np.seterr(all='ignore')

    def disambiguate(self, input):
      if self.disambiguationInProgress:
        try:
          input = re.sub('"', '', input.strip())
          index = int(input)-1    # since indices shown to user are incremented by 1
          movie = self.candidateMovies[index]
          self.disambiguationInProgress = False
          self.disambiguationJustResolved = True
          if self.cachedSentiment == 0:
            self.pendingMovie = (movie[1], self.fixDanglingArticle(movie[0]))
            return 'How did you feel about "{}"?'.format(movie[0])
          self.recentReviews[movie[0]] = self.cachedSentiment
          self.preferencesRecorded += 1 if self.userPreferencesVector[movie[1]] == 0 else 0   # increment if movie hasn't been rated by user yet
          self.userPreferencesVector[movie[1]] = self.cachedSentiment / abs(self.cachedSentiment)    # since we only want to store -1/1 for recommendations instead of the [-2, 2] scale
          return ''
        except:
          return enterNumBelowResponses[randint(0,len(enterNumBelowResponses)-1)] + self.getMatchingMovieOptions()


      allMovieMatches = self.extractMovieMatches(input)
      self.disambiguationInProgress = False
      for candidateMovieTuples in allMovieMatches.values():   # (title, id) tuple
        if len(candidateMovieTuples) > 1:
          self.candidateMovies = candidateMovieTuples
          self.disambiguationInProgress = True
          response = disambiguateMovieResponses[randint(0,len(disambiguateMovieResponses)-1)]
          self.updateSentimentDict(input)
          return response + self.getMatchingMovieOptions()

      return ''


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
