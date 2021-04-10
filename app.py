#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json, re, aiohttp, asyncio, string
from flask import Flask, request, jsonify, Response
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from resources.dutch_lexicon import dutch_lexicon
from src.models import AppStoreEntry, Review
from src.sentiments import Sentiments
from src.errors import InvalidUsage
from collections import Counter
import nltk

# ==============================================================================
# Properties definitions
# ==============================================================================

app = Flask(__name__)
analyzer = SentimentIntensityAnalyzer()
analyzer.lexicon.update(dutch_lexicon)
nltk.download('stopwords')

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
    stats = None

    validateAppStoreParameters(country, appID, pages)

    try:
        rawEntries = asyncio.run(get_appstore_reviews(country, appID, pages))
        entries = AppStoreEntry(many=True).load(rawEntries)
    except Exception as error:
        app.logger.error(f'Network error => {error}')
        raise InvalidUsage('Something went wrong while trying to fetch data from the AppStore', status_code=500)
    
    for entry in entries:
        title = entry['title']
        review = entry['review']
        documents = title + '. ' + review
        sentiments = Sentiments.analyse(documents, analyzer)
        compoundSentiment = sentiments['compound']
        entry['sentiment'] = compoundSentiment

    reviews = Review(many=True).dump(entries)
    jsonResponse = {"reviews" : reviews}

    try:
        stopwords = localStopwords(country)
        jsonResponse['statistics'] = calculateStatistics(entries, stopwords)
    except Exception as error:
        app.logger.warning(f'Statistics error => {error}')
        pass

    response = Response(json.dumps(jsonResponse))
    response.headers['Content-Type'] = 'application/json'
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

# ==============================================================================
# Utility functions
# ==============================================================================

def calculateStatistics(entries, stopwords):
    # Arrange
    averageSentiment = 0
    averageRating = 0
    textCorpus = ""
    stars = []
    ratings = {} 
    sentiments = {}
    statistics = {}

    # Iterate
    for entry in entries:
        averageSentiment += entry['sentiment']
        averageRating += entry['stars']
        stars.append(entry['stars'])
        key = entry['version']
        ratings[key] = ratings.get(key, []) + [entry['stars']]
        sentiments[key] = sentiments.get(key, []) + [entry['sentiment']]
        textCorpus += f"{entry['title']} {entry['review']} "

    # Process
    averageSentiment /= len(entries)
    averageRating /= len(entries)
    textCorpus = textCorpus.translate(str.maketrans('', '', string.punctuation))
    words = Counter(textCorpus.lower().split()).most_common(100)
    mostCommonWords = {w[0]: w[1] for w in words if w[0] not in stopwords}
    print(mostCommonWords)
    ratingDistribution = dict(Counter(stars).most_common(6))
    ratingPerVersion = dict(map(lambda v: (v[0], sum(v[1]) / len(v[1])), ratings.items()))
    sentimentPerVersion = dict(map(lambda v: (v[0], sum(v[1]) / len(v[1])), sentiments.items()))

    # Pack
    statistics['averageRating'] = averageRating
    statistics['averageSentiment'] = averageSentiment
    statistics['ratingPerVersion'] = ratingPerVersion
    statistics['sentimentPerVersion'] = sentimentPerVersion
    statistics['mostCommonWords'] = mostCommonWords
    statistics['ratingDistribution'] = ratingDistribution
    return statistics

def localStopwords(country):
    if country == 'nl':
        return nltk.corpus.stopwords.words('dutch')
    elif country == 'fr' or country == 'be':
        return nltk.corpus.stopwords.words('french')
    elif country == 'de':
        return nltk.corpus.stopwords.words('german')
    else:
        return nltk.corpus.stopwords.words('english')

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

