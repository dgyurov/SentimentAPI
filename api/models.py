#!/usr/bin/env python
# -*- coding: utf-8 -*-
from marshmallow import Schema, fields, pre_load

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
