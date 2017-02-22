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

from movielens import ratings
from random import randint
from PorterStemmer import PorterStemmer

class Chatbot:
    """Simple class to implement the chatbot for PA 6."""

    #############################################################################
    # `moviebot` is the default chatbot. Change it to your chatbot's name       #
    #############################################################################
    def __init__(self, is_turbo=False):
      self.name = 'Rudolfa'
      self.is_turbo = is_turbo
      self.read_data()
      self.p = PorterStemmer()
      self.sentimentDict = {} #movie to +/-1 , like/dislike
      self.titleDict = self.createTitleDict() #Movie ID to [title, genre]

    #############################################################################
    # 1. WARM UP REPL
    #############################################################################

    def greeting(self):
      """chatbot greeting message"""
      #############################################################################
      # TODO: Write a short greeting message                                      #
      #############################################################################

      greeting_message = 'Suh dude.'

      #############################################################################
      #                             END OF YOUR CODE                              #
      #############################################################################

      return greeting_message

    def goodbye(self):
      """chatbot goodbye message"""
      #############################################################################
      # TODO: Write a short farewell message                                      #
      #############################################################################
      r = randint(0,1)
      messages = {
        0 : 'See ya in a while crocodile :*',
        1 : 'Catch ya later alligator ;)'
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
      input = input.lower()
      self.updateSentimentDict(input)

    #   moviesAndGenres = []
    #   moviesAndGenres = self.returnMoviesAndGenres(self.extractMovies(input))

      if self.is_turbo == True:
        response = 'processed %s in creative mode!!' % input
      else:
        response = 'processed %s in starter mode' % input

      return response

    # Returns list of movies entered in input
    def extractMovies(self, input) :
        return re.findall(r'\"(.+?)\"', input)

    # Returns dict from input words to sentiments pos/neg
    def extractSentiment(self, input, src_file='data/sentiment.txt') :
        tokens = input.split()
        tokenSet = set(tokens)
        sentimentDict = self.sentiments(src_file, ',', csv.QUOTE_MINIMAL)
        tokensSentimentDict = {}
        for word in tokens:
            word = self.p.stem(word)
            if word in sentimentDict:
                tokensSentimentDict[word] = sentimentDict[word]
        return tokensSentimentDict

    # Returns sentiment.txt in dict form
    def sentiments(self, src_file, delimiter, quoting):
        reader = csv.reader(file(src_file), delimiter=delimiter, quoting=quoting)
        sentimentDict = {}
        for line in reader:
            word, sent = line[0], line[1]
            word = self.p.stem(word)
            sentimentDict[word] = sent
        return sentimentDict

    #Returns dict of movie ID to [title w/o year, genre]
    def createTitleDict(self):
        self.titles1, self.ratings = ratings()
        #Regex currently doesnt handle parenthesis in title.
            # Ex. "(500) Days of Summer"
        regexTitle = '([\w\s\',:\&¡!\*\]\[.-]*)(\s\(.*)?'
        titles = []
        for movie in self.titles1: # Create list of movie titles
            # print movie
            found = re.findall(regexTitle, movie[0], re.UNICODE)
            title = found[0][0].lower()
            length = len(title)
            if length != 0:
                if title[length - 1] == " ":
                    title = title[:-1]
                titles.append(title)

        idToTitleDict = {}
        for i, movie in enumerate(titles):
            idToTitleDict[i] = titles[i]
        return idToTitleDict

    #Classifies input as overall positive or negative and stores that in dict with movie ID
    def updateSentimentDict(self, input):
        binarySent = self.binarizeInputSentiment(input)
        for inputTitle in self.extractMovies(input):
            for id, title in self.titleDict.iteritems():
                if title == inputTitle: #What if movie is already in sentDict??
                    self.sentimentDict[id] = binarySent

    #Takes input, looks at sentiment words, computes overall sentiment based on
    #whether there are mor pos or neg words. returns pos if tie
    def binarizeInputSentiment(self, input):
        inputSentDict = {}
        inputSentDict = self.extractSentiment(input)
        negSum = 0
        posSum = 0
        for word in inputSentDict:
            if inputSentDict[word] == 'pos':
                posSum = posSum + 1
            else:
                negSum = negSum + 1
        if negSum > posSum:
            return -1
        else:
            return 1


    # def returnMoviesAndGenres(self, movieTitles): # Returns references to movies in movies.txt
    #     self.titles, self.ratings = ratings()  #Single title: [movieID, title, genres]
    #     # movieTitles = set(movieTitles)
    #     movieAndGenres = []
    #     regexTitle = '([\w\s\',:\&¡!.-]*)(\s\(.*)?'
    #     for movie in self.titles:
    #         found = re.findall(regexTitle, movie[0])
    #         title = found[0][0]
    #         # print movie
    #         length = len(title)
    #         if title[length - 1] == " ":
    #             title = title[:-1]
    #         print title + "@"
    #     #     if title[0] in movieTitles:
    #     #         print movie
    #     #         movieAndGenres.append(movie)
    #     #         movieTitles.remove(movie[0])
    #     # for movieLeftOver in movieTitles:
    #     #     print "Did not recognize the movie " + movieLeftOver
    #     return movieAndGenres







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


    def binarize(self):
      """Modifies the ratings matrix to make all of the ratings binary"""

      pass


    def distance(self, u, v):
      """Calculates a given distance function between vectors u and v"""
      # TODO: Implement the distance function between vectors u and v]
      # Note: you can also think of this as computing a similarity measure

      pass


    def recommend(self, u):
      """Generates a list of movies based on the input vector u using
      collaborative filtering"""
      # TODO: Implement a recommendation function that takes a user vector u
      # and outputs a list of movies recommended by the chatbot

      pass


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


if __name__ == '__main__':
    Chatbot()
