#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from resources.dutch_lexicon import dutch_lexicon

# ==============================================================================
# Sentiment analysis functions
# ==============================================================================
class Sentiments():
    
    @staticmethod
    def analyse(text):
        analyzer = SentimentIntensityAnalyzer()
        analyzer.lexicon.update(dutch_lexicon)
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

