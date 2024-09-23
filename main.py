# import libraries and set up Spotify credentials
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests
from bs4 import BeautifulSoup
import pandas as pd
from ratelimit import limits, sleep_and_retry
import re

@sleep_and_retry
@limits(calls=30, period=60)
# check API requests 
def check_limit():
    return

SP_ID = '961e75fad4924ed086b1880d8f10a91a'
SP_KEY = '5bf751cd234e4a9b932185784e538f4a'

# use Spotify API to retrieve albums given an artist
def get_albums(artist_name):
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=SP_ID, client_secret=SP_KEY))

    # search for artist given user input
    results = sp.search(q=artist_name, type='artist', limit=1)
    if len(results['artists']['items']) == 0:
        print("Artist not found on Spotify.")
        return []
    
    artist = results['artists']['items'][0]
    artist_id = artist['id']

    # retreive all album names
    albums = sp.artist_albums(artist_id, album_type='album')
    album_list = []
    for album in albums['items']:
        album_list.append(album['name'])
    
    return list(set(album_list))  # remove duplicates

# format provided names (adjust/remove special characters) for url
def format_url_string(name):
    formatted_name = name.lower().replace(' ', '-')
    formatted_name = re.sub(r'[\(\):]', '', formatted_name) 
    return re.sub(r'[^a-zA-Z0-9-]', '', formatted_name)

# scrape Pitchfork for album review
def scrape_pitchfork(artist_name, album_name):
    # format URL for the album review page
    artistF = format_url_string(artist_name)
    albumF = format_url_string(album_name)
    
    check_limit()
    url = f"https://pitchfork.com/reviews/albums/{artistF}-{albumF}/"
    
    response = requests.get(url)
    
    #error handling
    if response.status_code == 404:
        return None
    
    # use BeautifulSoup to parse album review
    soup = BeautifulSoup(response.text, 'html.parser')
    score = None
    
    score_tag = soup.find('div', class_='ScoreCircle-jAxRuP kFTFiL')
    if score_tag:
      score = score_tag.find('p').text.strip()
    # a different class if album is selected for best new music
    if not score_tag:
      score_tag = soup.find('div', class_='ScoreCircle-jAxRuP akdGf')
      if score_tag:
          score = score_tag.find('p').text.strip()
    if not score_tag:
      score_tag = soup.find('p', class_='BaseWrap-sc-gjQpdd BaseText-ewhhUZ Rating-bkjebD iUEiRd ffYgLc hGHFBC')
      if score_tag:
        score = score_tag.text.strip()  
    
    return {'Album': album_name, 'Score': score, 'Review Link': url}

# clean data and write to CSV
def write_to_csv(album_reviews):
    df = pd.DataFrame(album_reviews)
    df.to_csv('album_reviews.csv', index=False)
    print("Album reviews saved to album_reviews.csv")

# ask user to input an artist name 
def main():
    artist_name = input("Enter artist name: ")
    
    albums = get_albums(artist_name)
    
    if not albums:
        return
    
    print(f"Found {len(albums)} albums for {artist_name} on Spotify.")
    
    album_reviews = []
    
    # scrape Pitchfork for each album review
    for album in albums:
        review = scrape_pitchfork(artist_name, album)
        if review:
            album_reviews.append(review)
            print(f"Found review for {album}: {review['Score']}")
    
    if album_reviews:
    # write results to CSV
        write_to_csv(album_reviews)
    else:
        print("No reviews found for any albums.")

if __name__ == "__main__":
    main()
