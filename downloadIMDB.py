#!/usr/bin/env python
# -*- coding: utf-8 -*-

from imdb import IMDb
import pymongo
from pymongo import MongoClient
import re


def main():
  # initiating the imdb api
  ia = IMDb()
  
  # starting the client
  client = MongoClient()
       
  # getting the db for the imdb database
  db = client.imdb
  
  # getting the movie colletion
  movie_db = db.movies
  
  # all movies that were nominated
  movies = {} 
  movies['2014'] = ['Birdman: Or (The Unexpected Virtue of Ignorance)','American Sniper','Boyhood','The Grand Budapest Hotel','The Imitation Game','Selma','The Theory of Everything','Whiplash']
  movies['2013'] = ['American Hustle','Captain Phillips','Dallas Buyers Club','Gravity','Her','Nebraska','Philomena','The Wolf of Wall Street']
  movies['2012'] = ['Argo','Amour','Beasts of the Southern Wild','Django Unchained','Les Misérables','Life of Pi','Lincoln','Silver Linings Playbook','Zero Dark Thirty']
  movies['2011'] = ['The Artist','The Descendants','Extremely Loud & Incredibly Close','The Help','Hugo','Midnight in Paris','Moneyball','The Tree of Life','War Horse']
  movies['2010'] = ['The King\'s Speech','127 Hours','Black Swan','The Fighter','Inception','The Kids Are All Right','The Social Network','Toy Story 3','True Grit','Winter\'s Bone']
  movies['2009'] = ['The Hurt Locker','Avatar','The Blind Side','District 9','An Education','Inglourious Basterds','Precious','A Serious Man','Up','Up in the Air']
  movies['2008'] = ['Slumdog Millionaire','The Curious Case of Benjamin Button','Frost/Nixon','Milk','The Reader']
  movies['2007'] = ['No Country for Old Men','Atonement','Juno','Michael Clayton','There Will Be Blood']
  movies['2006'] = ['The Departed','Babel','Letters from Iwo Jima','Little Miss Sunshine','The Queen']
  movies['2005'] = ['Crash','Brokeback Mountain','Capote','Good Night, and Good Luck.','Munich']
  movies['2004'] = ['Million Dollar Baby','The Aviator','Finding Neverland','Ray','Sideways']
  movies['2003'] = ['The Lord of the Rings: The Return of the King','Lost in Translation','Master and Commander: The Far Side of the World','Mystic River','Seabiscuit']
  movies['2002'] = ['Chicago','Gangs of New York','The Hours','The Lord of the Rings: The Two Towers','The Pianist']
  movies['2001'] = ['A Beautiful Mind','Gosford Park','In the Bedroom','The Lord of the Rings: The Fellowship of the Ring','Moulin Rouge!']      
  movies['2000'] = ['Gladiator','Chocolat','Crouching Tiger', 'Hidden Dragon','Erin Brockovich','Traffic']      
    
  for year in movies:  
    for film in movies[year]:   
      if movie_db.find_one({'title':film}):
        print 'Movie already in mongodb'
        continue;
    
      s_result = ia.search_movie(film)
      
      if len(s_result) > 0:
        the_unt = s_result[0]
        #the_unt = ia.get_movie("0120667")
        
        #ia.update(the_unt)
        ia.update(the_unt)    
        ia.update(the_unt, 'business')      
       
        #saving movie
        movie_db.save(map_movie_to_dic(the_unt, int(year)))
      else:
        print 'No result for ' + film  

def getMoney(raw):
  regex = '\$([0-9],*)*'
  for item in raw:
    match = re.match(regex, item)
    if match:
      return int(match.group(0).strip('$').replace(',',''))  

def map_movie_to_dic(movie, year):
  movie_dic = {}
  movie_dic['_id'] = movie.movieID
  movie_dic['oscar_year'] = year
  map_person_list(movie,movie_dic,'assistant director')
  map_person_list(movie,movie_dic,'director')   
  map_person_list(movie,movie_dic,'writer')  
  map_person_list(movie,movie_dic,'editor')
  map_person_list(movie,movie_dic,'cast') 
  map_person_list(movie,movie_dic,'editor') 
  map_person_list(movie,movie_dic,'original music')
  map_company_list(movie,movie_dic,'distributors')
  map_company_list(movie,movie_dic,'production companies')  
  map_company_list(movie,movie_dic,'special effects companies')         
  map_person_list(movie,movie_dic,'casting director')          
  movie_dic['title'] = movie['title']
  if 'plot' in movie.data:
    movie_dic['plot'] = movie['plot']
  movie_dic['user_rating'] = movie['rating']
  movie_dic['countries'] = movie['countries']
  movie_dic['genres'] = movie['genres']      
  movie_dic['runtime'] = movie['runtime']
  movie_dic['languages'] = movie['languages']  
  if 'opening weekend' in movie['business']:
    movie_dic['opening_weekend'] = getMoney(movie['business']['opening weekend'])
  else:
    movie_dic['opening_weekend'] = 0  
  if 'budget' in movie['business']:
    movie_dic['budget'] = getMoney(movie['business']['budget'])
  else:
    movie_dic['budget'] = 0
  
  print 'Saving the movie ' + movie_dic['title']
  return movie_dic
  
def map_person_list(movie,movie_dic,field):
  movie_dic[field] = []  
  if field in movie.data:
    for person in movie[field]:    
      subdoc = {}
      subdoc['name'] = person['name']
      subdoc['id'] = person.personID    
      movie_dic[field].append(subdoc)
    
def map_company_list(movie,movie_dic,field):
  movie_dic[field] = []  
  if field in movie.data:
    for person in movie[field]:    
      subdoc = {}
      subdoc['name'] = person['name']
      subdoc['id'] = person.companyID    
      movie_dic[field].append(subdoc)        

if __name__ == "__main__":
    main()
