#!/usr/bin/env python
# -*- coding: utf-8 -*-
from marshmallow import Schema, fields, pre_load, pre_dump, EXCLUDE
from datetime import datetime

# ==============================================================================
# Schema definitions
# ==============================================================================

class Review(Schema):
    class Meta:
        unknown = EXCLUDE

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
    def move_title(self, data, **kwargs):  
        if not data['title']:
            data.pop('title')
            return data
        
        return data

    @pre_dump
    def move_name(self, data, **kwargs):
        if not data['name']:
            data['name'] = 'Unknown user'
            return data

        return data

class AppStoreEntry(Schema):
    class Meta:
        unknown = EXCLUDE
        partial = True
    
    id = fields.Str()
    name = fields.Str()
    title = fields.Str()
    review = fields.Str()
    stars = fields.Int()
    version = fields.Str()

    @pre_load
    def move_id(self, data, **kwargs):
        id = data.pop('id')
        data['id'] = id['label']
        return data

    @pre_load
    def move_name(self, data, **kwargs):
        author = data.pop('author')
        name = author.pop('name')
        data['name'] = name['label']
        return data

    @pre_load
    def move_title(self, data, **kwargs):
        title = data.pop('title')
        data['title'] = title['label']
        return data

    @pre_load
    def move_review(self, data, **kwargs):
        content = data.pop('content')
        data['review'] = content['label']
        return data

    @pre_load
    def move_stars(self, data, **kwargs):
        rating = data.pop('im:rating')
        data['stars'] = int(rating['label'])
        return data

    @pre_load
    def move_version(self, data, **kwargs):
        version = data.pop('im:version')
        data['version'] = version['label']
        return data

