#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests, json, re
from flask import Flask, request, jsonify, Response
from models import AppStoreEntry, PlayStoreEntry, Review
from sentiments import Sentiments
from errors import InvalidUsage

# ==============================================================================
# Properties definitions
# ==============================================================================

app = Flask(__name__)

# ==============================================================================
# Routes
# ==============================================================================

@app.route("/apple/reviews", methods=['GET'])
def appleReviews():
    return handleAppleReviews()

@app.route("/android/reviews", methods=['GET'])
def androidReviews():
    return handleAndroidReviews()


# ==============================================================================
# Route handling
# ==============================================================================

def handleAppleReviews():
    country = request.args.get('country')
    appID = request.args.get('appID')
    validateAppStoreParameters(country, appID)

    url = f"https://itunes.apple.com/{country}/rss/customerreviews/page=1/id={appID}/sortby=mostrecent/json"

    try:
        response = requests.get(url, headers={'Content-Type': 'application/json'})
        jsonEntries = json.loads(response.content)['feed']['entry']
    except:
        raise InvalidUsage('Something went wrong while trying to fetch data from the AppStore', status_code=500)
    
    entries = AppStoreEntry(many=True).load(jsonEntries).data

    for entry in entries:
        title = entry['title']
        review = entry['review']
        documents = title + '. ' + review
        sentiments = Sentiments.analyse(documents)
        compoundSentiment = sentiments['compound']
        entry['sentiment'] = compoundSentiment

    reviews = Review(many=True).dumps(entries)

    response = Response(reviews.data)
    response.headers['Content-Type'] = 'application/json'
    return response

def handleAndroidReviews():
    appID = request.args.get('appID')
    validatePlayStoreParameters(appID)

    url = f"https://still-plateau-10039.herokuapp.com/reviews?id={appID}"

    try:
        response = requests.get(url, headers={'Content-Type': 'application/json'})
        jsonEntries = json.loads(response.content)
    except:
        raise InvalidUsage('Something went wrong while trying to fetch data from the PlayStore', status_code=500)
    
    entries = PlayStoreEntry(many=True).load(jsonEntries).data
    
    for entry in entries:
        title = entry['title']
        review = entry['review']
        documents = title + '. ' + review
        sentiments = Sentiments.analyse(documents)
        compoundSentiment = sentiments['compound']
        entry['sentiment'] = compoundSentiment

    reviews = Review(many=True).dumps(entries)

    response = Response(reviews.data)
    response.headers['Content-Type'] = 'application/json'
    return response

# ==============================================================================
# Error handling
# ==============================================================================

@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

def validateAppStoreParameters(country, appID):
    if not country:
        raise InvalidUsage('Country is a mandatory parameter for getting Apple Reviews', status_code=400)

    if not re.match(r'^[\w\d]+$', country):
        raise InvalidUsage('Country contains illigal characters', status_code=400)

    if not appID:
        raise InvalidUsage('appID is a mandatory parameter for getting Apple Reviews', status_code=400)
    
    if not re.match(r'^[\w\d]+$', appID):
        raise InvalidUsage('appID contains illigal characters', status_code=400)

def validatePlayStoreParameters(appID):
    if not appID:
        raise InvalidUsage('appID is a mandatory parameter for getting PlayStore Reviews', status_code=400)
    
    if not re.match(r'^([A-Za-z]{1}[A-Za-z\d_]*\.)*[A-Za-z][A-Za-z\d_]*$', appID):
        raise InvalidUsage('appID is an illigal Android application id', status_code=400)


