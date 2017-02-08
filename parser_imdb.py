# -*- coding: utf-8 -*-
# iMDB 2 JSON-LD
# © 2015/07 Wladston Viana (wladston@wladston.net) under the BSD License.
#
# WHAT IS THIS SCRIPT
# This script converts a SQLite-based iMDB dataset to the JSON-LD format using
# the schema.org vocabulay. Expects a "imdb.sqlite" database file at the
# working directory. Also make sure you have all the python requirements (see
# requirements.txt).
#
# TODO:
# - Make sure all the information from Person is properly implemented.
# - Caching: never process person or company twice.
# - Create final bash script to:
#       -- Download the needed files from imdb servers. (20)
#       -- Generates the sql database (10)
#       -- Converts the sql datbase to json-ld data. (10)
#       -- Create requirements.txt
#
# - Map the keys certificates, mpaa to schema:contentRatig.
# - Map the key certificates to schema:typicalAgeRange.
# - Map the key literature to schema:referecedIn.
# - Map the key ['business']['copyright holder'] to schema:copyrightHolder.
# - Fix representation of schema:birthDate.
# - Fix representation of schema:ratingValue, use decimal instead of float.
# - Fix representation of schema:duration.
# - Review the get_movie_duration() function.
#
# NOTE: These keys, even though available on the iMDB dataset, were not used so
# far because they do not fit in the schema.org vocabulary.
# 'color info', 'crazy credits', 'complete crew', 'complete cast', 'trivia',
# 'sound mix', 'tech info', 'quotes', 'votes distribution', 'countries',
# 'goofs', 'laserdisc', 'canonical title', 'long imdb title', 'long imdb
# canonical title', 'smart canonical title', 'smart long imdb canonical title',


# Python Libs.
import os
import re
import json
import sqlite3
from datetime import datetime, timedelta

# External Libs.
from dateutil.parser import parse as duparser
from pyld import jsonld
from imdb import IMDb


def setup_session():
    path = os.path.dirname(os.path.realpath(__file__)) + "/imdb.sqlite"
    db = sqlite3.connect(path)
    imdb = IMDb('sql', uri='sqlite://' + path)
    return db.cursor(), imdb


def get_imdb_url(element, element_type=None, resolve_using_imdb=False):
    if not resolve_using_imdb:
        # URL Format: http://www.imdb.com/Title?Bourne+Ultimatum,+The+(2007)
        # http://www.imdb.com/Name?Musgrove,+Matt
        base = 'http://www.imdb.com/%s' % (element_type)
        key = 'long imdb canonical %s' % element_type.lower()
        url = base + '?' + element[key]
        return url.replace(' ', '+')
    else:
        return IA.get_imdbURL(x)

def get_and_parse_companies(imdb, movie):
    need_type = ['distributors']
    companies = {}

    for role in ['production companies', 'distributors']:
        for company in movie.get(role, []):
            imdb.update(company, info=['main'])
            cdata = {'name': company['name']}
            if company.get('country'):
                c = company['country']
                if c[0] == '[' and c[-1] == ']':
                    c = c[1:-1]
                cdata['address'] = {'addressCountry': c}
            if role in need_type:
                cdata['@type'] = 'Organization'
            companies.setdefault(role, []).append(cdata)
    return companies

def get_rating(movie):
    return {'ratingCount': movie['votes'],
            'bestRating': 10,
            'worstRating': 1,
            'ratingValue': movie['rating']}


def parse_imdb_team(team, role):
    people = []
    need_type = ['producer', 'composer', 'writer']
    for pdata in [p for p in team.values() if role in p['roles']]:
        person = {'@id': get_imdb_url(pdata, 'Name')}
        person['name'] =  pdata['name'],
        if 'height' in pdata:
            person['height'] = {'@type': 'QuantitativeValue',
                                'unitText': pdata['height']}
        if 'birth date' in pdata:
            person['birthDate'] = pdata['birth date']

        if 'birth notes' in pdata:
            person['birthPlace'] = {'@type': 'Place',
                                    'name': pdata['birth notes']}
        if role in need_type:
            person['@type'] = 'Person'

        people.append(person)
    return people


def get_team(imdb, movie):
    '''Extracts all people participating in producing the movie.'''
    special = ['producer', 'writer', 'cast', 'director', 'editor', 'composer']

    not_special = ['sound crew', 'art department', 'visual effects', 'make up',
        'art director', 'set decorator', 'costume designer', 'cinematographer',
        'stunt performer', 'production designer', 'production manager',
        'assistant director', 'crewmembers']

    team = {}
    for role in special + not_special:
        for person in movie.get(role, []):
            imdb.update(person, info=['biography', 'main'])
            cname = person['long imdb canonical name']
            person.data['long imdb canonical name'] = cname
            team.setdefault(person.getID(), person.data)
            role = 'contributor' if role in not_special else role
            team[person.getID()].setdefault('roles', []).append(role)

    for person in team.values():
        if 'contributor' in person['roles'] and len(person['roles']) > 1:
            person['roles'].remove('contributor')
    return team

def get_movie_duration(m):
    if 'runtimes' in m.keys():
        runtime = m['runtimes'][0]

        if '::' in runtime:
            runtime = runtime.split('::')[0]

        if ':' in runtime:
            runtime = runtime.split(':')[1]

        if '.' in runtime:
            runtime = runtime.split('.')[0]

        if '-' in runtime:
            runtime = runtime.split('-')[0]

        if ',' in runtime:
            runtime = runtime.split(',')[0]

        if ' ' in runtime:
            runtime = runtime.split(' ')[0]

        if '\'' in runtime:
            runtime = runtime.split('\'')[0]

        if '\"' in runtime:
            runtime = runtime.split('\"')[0]

        if 'm' in runtime:
            runtime = runtime.split('m')[0]

        if '\\' in runtime:
            runtime = runtime.split('\\')[0]

        if '/' in runtime:
            runtime = runtime.split('/')[0]

        if runtime == '':
            return None

        runtime = int(runtime)

        return str(timedelta(minutes=runtime))

    return None

def get_movie_release(movie):
    if movie.get('release dates'):
        return str(duparser(movie['release dates'][0].split(':')[1]).date())
    elif movie.get('year'):
        return str(datetime.strptime(str(movie['year']), '%Y').date())
    return None


def get_headlines(movie):
    if not movie.get('taglines'):
        return None, None
    if len(movie['taglines']) == 1:
        return movie['taglines'][0], None
    else:
        return movie['taglines'][1], movie['taglines'][1:]


def get_alternate_name(movie):
    alternate_name = []
    for title in movie.get('akas',[]):
        title = title.split('::')[0]
        mth = re.match( r'^(.*)\([0-9]{4}\)$', title)
        title = mth.group() if mth else title
        alternate_name.append(title.strip())

    return alternate_name


def fetch_imdb_object(imdb, mid):
    # Unused_infosets:
    # 'alternate versions', 'connections', 'crazy credits', 'episodes','goofs',
    # 'technical', 'literature', 'locations', 'quotes', 'trivia',
    # 'vote details'
    infosets = ['business', 'main', 'plot', 'keywords','release dates',
                'soundtrack', 'taglines']
    return imdb.get_movie(mid, info=infosets)

def parse_imdb_movie(movie):
    movie['duration'] = get_movie_duration(movie)
    movie['aggregateRating'] = get_rating(movie)
    movie['headline'], movie['alternativeHeadline'] = get_headlines(movie)
    movie['datePublished'] = get_movie_release(movie)
    movie['genre'] = ', '.join(movie.get('genres', []))
    movie['inLanguage'] = ', '.join(movie.get('languages', []))
    movie['keywords'] = ','.join(movie.get('keywords', []))
    movie['alternateName'] = get_alternate_name(movie)
    movie['description'] = movie.get('plot', [])[0]
    movie['name'] = movie['title']
    movie['url'] = get_imdb_url(movie, 'Title')

    return movie


def get_movies_to_process(cursor):
    # kind_id = 1 is for cinema entries.
    # info_type_id = 100 is for number of votes.
    min_votes = 128000
    q = """ SELECT id FROM title WHERE kind_id = 1
            AND id IN (SELECT DISTINCT movie_id FROM movie_info_idx WHERE
                       info_type_id = 100 AND CAST(info as int) > %d);"""
    ids = cursor.execute(q % min_votes).fetchall()
    print "// %d movies to process." % len(ids)
    return [x[0] for x in ids]


def get_jsonld_from_imdb(imdb, mid):
    imdb_movie = fetch_imdb_object(imdb, mid)
    imdb_team = get_team(imdb, imdb_movie)
    companies = get_and_parse_companies(imdb, imdb_movie)
    movie_data = parse_imdb_movie(imdb_movie)

    movie = {
        '@id': movie_data['url'],
        '@type': 'Movie',
        'actor': parse_imdb_team(imdb_team, 'cast'),
        'director': parse_imdb_team(imdb_team, 'director'),
        'duration': movie_data['duration'],
        'musicBy': parse_imdb_team(imdb_team, 'composer'),
        'productionCompany': companies['production companies'],
        'aggregateRating': movie_data['aggregateRating'],
        'alternativeHeadline': movie_data['alternativeHeadline'],
        'author': parse_imdb_team(imdb_team, 'writer'),
        'datePublished': movie_data['datePublished'],
        'editor': parse_imdb_team(imdb_team, 'editor'),
        'genre': movie_data['genre'],
        'headline': movie_data['headline'],
        'inLanguage': movie_data['inLanguage'],
        'keywords': movie_data['keywords'],
        'producer': parse_imdb_team(imdb_team, 'producer'),
        'provider': companies['distributors'],
        'alternateName': movie_data['alternateName'],
        'description': movie_data['description'],
        'name': movie_data['name'],
        'url': movie_data['url'],
    }

    return {k: v for (k, v) in movie.items() if v}


def process_all_imdb(cursor, imdb):
    for i, mid in enumerate(get_movies_to_process(cursor)):
        print "// %d movies processed." % i
        movie = get_jsonld_from_imdb(imdb, mid)

        movie = jsonld.compact(movie, 'http://schema.org/')
        print json.dumps(movie, indent=4)

if __name__ == "__main__":
    cursor, imdb = setup_session()
    process_all_imdb(cursor, imdb)

