#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nltk.sentiment.vader import SentimentIntensityAnalyzer
from flask import Flask, request, abort
from marshmallow import Schema, fields, pprint
from googletrans import Translator
import json, re

# ==============================================================================
# Schema definitions
# ==============================================================================

class SentimentSchema(Schema):
    text = fields.String()
    compound = fields.Float()
    negative = fields.Float()
    neutral = fields.Float()
    positive = fields.Float()

class SentimentCollectionSchema(Schema):
    sentiments = fields.Nested(SentimentSchema(), many=True)
    count = fields.Int()
    compound = fields.Float()
    negative = fields.Float()
    neutral = fields.Float()
    positive = fields.Float()

class SentimentResultsSchema(Schema):
    results = fields.Nested(SentimentCollectionSchema(), many=True)

class TranslationResultsSchema(Schema):
    results = fields.List(fields.String())

# ==============================================================================
# Properties definitions
# ==============================================================================

app = Flask(__name__)
translator = Translator()
analyzer = SentimentIntensityAnalyzer()
collectionSchema = SentimentCollectionSchema()
resultsSchema = SentimentResultsSchema()
translationResultsSchema = TranslationResultsSchema()

# ==============================================================================
# Application routes
# ==============================================================================

@app.route("/translations", methods=['POST'])
def translations():
    jsonData = request.json
    documents = jsonData['documents']
    results = []
        
    if len(documents) == 0:
        abort(400)

    translations = translator.translate(documents, dest='en')

    for translation in translations:
        results.append(translation.text)

    return translationResultsSchema.dumps(dict(results=results))

@app.route('/sentiments', methods=['POST'])
def sentiments():
    jsonData = request.json
    documents = jsonData['documents']
    results = []

    if len(documents) == 0:
        abort(400)

    for document in documents:
        documentjson = sentiment(document)
        results.append(documentjson)

    return resultsSchema.dumps(dict(results=results))

# ==============================================================================
# Helper functions
# ==============================================================================

def sentiment(text):
    sentences_list = filter(None, re.split("[.!?]+",text))
    count = len(sentences_list)
    sentiments_list = []
    compound = 0
    negative = 0
    neutral = 0
    positive = 0

    for sentence in sentences_list:
        result = analyzer.polarity_scores(sentence)
        compound += result["compound"]
        negative += result["neg"]
        neutral += result["neu"]
        positive += result["pos"]
        sentiment = dict(text=text, compound=result["compound"], negative=result["neg"], neutral=result["neu"], positive=result["pos"])
        sentiments_list.append(sentiment)

    return dict(sentiments=sentiments_list, count=count, compound=compound/count, negative=negative/count, neutral=neutral/count, positive=positive/count)
