#!/usr/bin/env python
# -*- coding: utf-8 -*-
from marshmallow import Schema, fields, pre_load, pre_dump
from datetime import datetime

# ==============================================================================
# Schema definitions
# ==============================================================================

class Review(Schema):
    class Meta:
        unknown = 'EXCLUDE'

    name = fields.Str()
    title = fields.Str(required=False)
    review = fields.Str()
    stars = fields.Int()
    sentiment = fields.Float()
    date = fields.Str(required=False)
    version = fields.Str(required=False)
    id = fields.Str()
    reply = fields.Str(required=False)

    @pre_dump
    def move_title(self, data):  
        if not data['title']:
            data.pop('title')
            return data
        
        return data

    @pre_dump
    def move_name(self, data):
        if not data['name']:
            data['name'] = 'Unknown user'
            return data

        return data

class AppStoreEntry(Schema):
    class Meta:
        unknown = 'EXCLUDE'
        partial = True
    
    id = fields.Str()
    name = fields.Str()
    title = fields.Str()
    review = fields.Str()
    stars = fields.Int()
    version = fields.Str()

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

class PlayStoreEntry(Schema):
    class Meta:
        unknown = 'EXCLUDE'
        partial = True
    
    id = fields.Str()
    name = fields.Str()
    date = fields.Str()
    stars = fields.Int()
    title = fields.Str()
    review = fields.Str()
    reply = fields.Str()

    @pre_load
    def move_name(self, data):
        userName = data.pop('userName')
        data['name'] = userName
        return data

    @pre_load
    def move_stars(self, data):
        score = data.pop('score')
        data['stars'] = score
        return data
    
    @pre_load
    def move_review(self, data):
        text = data.pop('text')
        data['review'] = text
        return data

    @pre_load
    def move_reply(self, data):
        if not 'replyText' in data:
            return data
        
        replyText = data.pop('replyText')
        data['reply'] = replyText
        return data

