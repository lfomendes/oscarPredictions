# -*- coding: utf-8 -*-
# Linkedmdb 2 JSON-LD
# © 2015/07 Wladston Viana (wladston@wladston.net) under the BSD License.
#
# WHAT IS THIS SCRIPT
# This script converts data served by LinkedMDB into a JSON-LD format using the
# schema.org vocabulay. Make sure you have all the python requirements (see
# requirements.txt).
#
# TODO: The lack of triple dump problem:
# Ideally, we would replace "ldbfilm:1026" in our sparql query to ?movie and
# have the endpoint give is the complete information for all triples. If you
# try to do this, you'll DDOS-crash their endpoint for a few minutes and still
# won't get any reply. We need a way to fix this issue.


from SPARQLWrapper import SPARQLWrapper, Wrapper
from rdflib import Graph
from pyld import jsonld
import json
import sys

sparql = SPARQLWrapper("http://data.linkedmdb.org/sparql")
sparql.setQuery("""

PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX dc: <http://purl.org/dc/terms/>
PREFIX ldbmovie: <http://data.linkedmdb.org/resource/movie/>
PREFIX ldbfilm: <http://data.linkedmdb.org/resource/film/>
PREFIX ldbdir: <http://data.linkedmdb.org/resource/director/>
PREFIX : <http://schema.org/>

CONSTRUCT {
  ldbfilm:465  a               :Movie       ;
               :name           ?movie_name  ;
               :actor          ?actor       ;
               :director       ?director    ;
               :duration       ?runtime     ;
               :contentRating  ?rating_str  ;
               :author         ?writer      ;
               :editor         ?editor      ;
               :datePublished  ?release     ;
               :genre          ?genre_name  ;
               :inLanguage     ?lang        ;
               :producer       ?producer_e  ;
               :producer       ?producer    ;
               :provider       ?dist_rel    ;
               :sameAs         ?sameas      .


  ?actor :name ?actor_name .
  ?actor a     :Person     .

  ?dist_rel a :Organization .
  ?dist_rel :name ?dist     .

  ?editor :name ?editor_name .
  ?editor a     :Person      .

  ?producer_e :name ?producer_e_name .
  ?producer_e a     :Person          .

  ?producer :name ?producer_name .
  ?producer a     :Person        .

  ?director :name  ?director_name .
  ?director  a     :Person        .

  ?writer :name ?writer_name .
  ?writer a     :Person      .
}
WHERE {
  ldbfilm:1026 dc:title ?movie_name .
  OPTIONAL {
    ldbfilm:465  ldbmovie:actor                ?actor      ;
                 ldbmovie:director             ?director   ;
                 ldbmovie:writer               ?writer     ;
                 ldbmovie:editor               ?editor     ;
                 ldbmovie:runtime              ?runtime    ;
                 ldbmovie:rating               ?rating     ;
                 ldbmovie:initial_release_date ?release    ;
                 ldbmovie:genre                ?genre      ;
                 ldbmovie:language             ?lang       ;
                 ldbmovie:executive_producer   ?producer_e ;
                 ldbmovie:producer             ?producer   ;
                 foaf:page                     ?sameas     .

    ?dstr ldbmovie:film_of_distributor                            ldbfilm:465 ;
          ldbmovie:film_film_distributor_relationship_distributor ?dist .

    ?actor ldbmovie:actor_name ?actor_name .

    ?producer_e ldbmovie:producer_name ?producer_e_name .

    ?producer ldbmovie:producer_name ?producer_name .

    ?rating ldbmovie:content_rating_name ?rating_str .

    ?genre ldbmovie:film_genre_name ?genre_name .

    ?director ldbmovie:director_name ?director_name .
  }
}
""")

# As os july/2015, LinkedMDB's sparql endpoint did not support JSON-LD.
sparql.setReturnFormat(Wrapper.N3)
response = sparql.query()

if 'response' not in dir(response):
  print response
  sys.exit()

n3 = "".join(response.response.readlines())

print n3

g = Graph()
movie = json.loads(g.parse(data=n3, format='n3').serialize(format='json-ld'))

context = 'http://schema.org/'
movie = jsonld.compact(movie, {'@context': context})
print json.dumps(movie, indent=4)
