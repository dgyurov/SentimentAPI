#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json, re, aiohttp, asyncio
from flask import Flask, request, jsonify, Response
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from resources.dutch_lexicon import dutch_lexicon
from src.models import AppStoreEntry, Review
from src.sentiments import Sentiments
from src.errors import InvalidUsage

# ==============================================================================
# Properties definitions
# ==============================================================================

app = Flask(__name__)
analyzer = SentimentIntensityAnalyzer()
analyzer.lexicon.update(dutch_lexicon)

# ==============================================================================
# Routes
# ==============================================================================

@app.route("/apple/reviews", methods=['GET'])
def appleReviews():
    return handleAppleReviews()

# ==============================================================================
# Route handling
# ==============================================================================

def handleAppleReviews():
    country = request.args.get('country')
    appID = request.args.get('appID')
    pages = request.args.get('pages')
    pages = 1 if pages is None else int(pages)

    validateAppStoreParameters(country, appID, pages)

    try:
        rawEntries = asyncio.run(get_appstore_reviews(country, appID, pages))
        entries = AppStoreEntry(many=True).load(rawEntries)
    except:
        raise InvalidUsage('Something went wrong while trying to fetch data from the AppStore', status_code=500)
    
    for entry in entries:
        title = entry['title']
        review = entry['review']
        documents = title + '. ' + review
        sentiments = Sentiments.analyse(documents, analyzer)
        compoundSentiment = sentiments['compound']
        entry['sentiment'] = compoundSentiment

    reviews = Review(many=True).dump(entries)
    
    response = Response(json.dumps({"reviews": reviews}))
    response.headers['Content-Type'] = 'application/json'
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

async def fetch_appstore_reviews(session, url):
    async with session.get(url) as resp:
        reviews = await resp.text()
        return json.loads(reviews)['feed']['entry']

async def get_appstore_reviews(country, appID, pages):
    async with aiohttp.ClientSession() as session:
        tasks = []

        for page in range(1, pages + 1):
            url = f"https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={appID}/sortby=mostrecent/json"
            tasks.append(asyncio.create_task(fetch_appstore_reviews(session, url))) 
        
        jsonEntries = await asyncio.gather(*tasks)
        return [item for sublist in jsonEntries for item in sublist]

# ==============================================================================
# Error handling
# ==============================================================================

@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

# ==============================================================================
# Validation
# ==============================================================================

def validateAppStoreParameters(country, appID, pages):
    if not country:
        raise InvalidUsage('Country is a mandatory parameter for getting Apple Reviews', status_code=400)

    if not re.match(r'^[\w\d]+$', country):
        raise InvalidUsage('Country contains illigal characters', status_code=400)

    if not appID:
        raise InvalidUsage('appID is a mandatory parameter for getting Apple Reviews', status_code=400)
    
    if not re.match(r'^[\w\d]+$', appID):
        raise InvalidUsage('appID contains illigal characters', status_code=400)

    if pages < 1 or pages > 10:
        raise InvalidUsage('pages must be between 1 and 10', status_code=400)

