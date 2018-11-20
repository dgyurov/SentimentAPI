#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nltk.sentiment.vader import SentimentIntensityAnalyzer
from flask import Flask, request, abort
from marshmallow import Schema, fields, pprint, pre_load
from py_translator import Translator
import json, re, datetime
import requests

# ==============================================================================
# Schema definitions
# ==============================================================================
class Review(Schema):
    class Meta:
        unknown = 'EXCLUDE'

    name = fields.Str(required=True)
    title = fields.Str(required=True)
    titleEnglish = fields.Str()
    review = fields.Str(required=True)
    reviewEnglish = fields.Str()
    stars = fields.Int(required=True)
    sentiment = fields.Float(required=True)
    date = fields.Date()
    version = fields.Str(required=True)
    id = fields.Str(required=True)
    reply = fields.Str()

class AppStoreEntry(Schema):
    class Meta:
        unknown = 'EXCLUDE'
        partial = True
    
    id = fields.Str(load_from='id.label')
    name = fields.Str(load_from='author.name.label')
    title = fields.Str(load_from='title.label')
    review = fields.Str(load_from='content.label')
    stars = fields.Int(load_from='im:rating.label')
    version = fields.Str(load_from='im:version.label')

    @pre_load
    def move_id(self, data):
        id = data.pop('id')
        data['id'] = id['label']
        return data

    @pre_load
    def move_name(self, data):
        author = data.pop('author')
        name = author.pop('name')
        data['name'] = name['label']
        return data

    @pre_load
    def move_title(self, data):
        title = data.pop('title')
        data['title'] = title['label']
        return data

    @pre_load
    def move_review(self, data):
        content = data.pop('content')
        data['review'] = content['label']
        return data

    @pre_load
    def move_stars(self, data):
        rating = data.pop('im:rating')
        data['stars'] = int(rating['label'])
        return data

    @pre_load
    def move_version(self, data):
        version = data.pop('im:version')
        data['version'] = version['label']
        return data

# ==============================================================================
# Properties definitions
# ==============================================================================

app = Flask(__name__)
analyzer = SentimentIntensityAnalyzer()

# ==============================================================================
# Application routes
# ==============================================================================

@app.route("/reviews", methods=['GET'])
def reviews():
    headers = {'Content-Type': 'application/json'}
    # TestFlight in US AppStore
    response = requests.get("https://itunes.apple.com/us/rss/customerreviews/page=1/id=899247664/sortby=mostrecent/json", headers=headers)
    jsonEntries = json.loads(response.content)['feed']['entry']
    entries = AppStoreEntry(many=True).load(jsonEntries).data

    for entry in entries:
        title = entry['title']
        review = entry['review']
        documents = title + '. ' + review
        # documentsString = entry['title'] + entry['review']
        sentiments = sentiment(documents)
        compoundSentiment = sentiments['compound']
        entry['sentiment'] = compoundSentiment


    return Review(many=True).dumps(entries)

# ==============================================================================
# Helper functions
# ==============================================================================

def sentiment(text):
    sentences_list = list(filter(None, re.split("[.!?]+", text)))
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
        sentiment = dict(text=sentence, compound=result["compound"], negative=result["neg"], neutral=result["neu"], positive=result["pos"])
        sentiments_list.append(sentiment)

    return dict(sentiments=sentiments_list, count=count, compound=compound/count, negative=negative/count, neutral=neutral/count, positive=positive/count)
