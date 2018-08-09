#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nltk.sentiment.vader import SentimentIntensityAnalyzer
from flask import Flask, request, abort
from marshmallow import Schema, fields, pprint
import translate, re
import json

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
analyzer = SentimentIntensityAnalyzer()
collectionSchema = SentimentCollectionSchema()
resultsSchema = SentimentResultsSchema()
translationResultsSchema = SentimentResultsSchema()
separator = "{|[***]|}"

# ==============================================================================
# Application routes
# ==============================================================================

@app.route("/translations", methods=['POST'])
def translateSentiments():
    jsonData = request.json
    documents = jsonData['documents']
    to_lang = jsonData["to_lang"]
    from_lang = jsonData["from_lang"]
    translator = translate.Translator(from_lang=from_lang, to_lang=to_lang)
    text = separator.join(documents)
    translated_text = translator.translate(text)
    results = translated_text.split(separator) 
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
