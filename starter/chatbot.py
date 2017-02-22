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
      r = random.randomInt(0,1)
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
      #############################################################################
      # TODO: Implement the extraction and transformation in this method, possibly#
      # calling other functions. Although modular code is not graded, it is       #
      # highly recommended                                                        #
      #############################################################################
      movieTitles = [] #List of movie titles included in double quotations
      sentimentWords = [] #Dictionary of words in input that have an associated sentiment
      movieTitles += self.extractMovies(input)
      sentimentWords += self.extractSentiment(input)

      print movieTitles
      print sentimentWords

      if len(movieTitles) == 5:
        self.recommend()

      # if self.is_turbo == True:
      #   response = 'processed %s in creative mode!!' % input
      # else:
      #   response = 'processed %s in starter mode' % input

      return ""

    def extractMovies(self, input) :
        return re.findall(r'\"(.+?)\"', input)

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

    def sentiments(self, src_file, delimiter, quoting):
        reader = csv.reader(file(src_file), delimiter=delimiter, quoting=quoting)
        sentimentDict = {}
        for line in reader:
            word, sent = line[0], line[1]
            word = self.p.stem(word)
            sentimentDict[word] = sent
        return sentimentDict


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
      if result > 0.0:
        return 1
      elif result < 0.0:
        return -1
      return 0


    def sim(self, u, v):
      """Calculates a given distance function between vectors u and v"""
      commonMovies = set(u.keys()).union(set(v).keys())
      meanU = sum(u.values()) / float(len(u.values()))
      meanV = sum(v.values()) / float(len(v.values()))
      deviationU = 0.0
      deviationV = 0.0
      stdU = 0.0
      stdV = 0.0
      for movie in commonMovies:
        deviationU += u[movie] - meanU
        deviationV = v[movie] - meanV
        stdU += (u[movie] - meanU)**2
        stdV += (v[movie] - meanV)**2

      return (deviationU * deviationV) / sqrt(stdU * stdV)  


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
