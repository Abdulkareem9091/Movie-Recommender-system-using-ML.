import os
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("API_KEY")

import pickle
import streamlit as st
import requests
import time


@st.cache_data
def fetch_data(url): 
    try: return requests.get(url, timeout=10).json()
    except requests.exceptions.RequestException: return {}

def fetch_movie_details(movie_id):
    data = fetch_data(f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}")
    if not data: return {}
    poster_url = f"https://image.tmdb.org/t/p/w500/{data.get('poster_path', 'default_poster.jpg')}"
    trailer_url = next((f"https://www.youtube.com/watch?v={video['key']}&autoplay=1&controls=0" for video in fetch_data(f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={API_KEY}").get('results', []) if video['site'] == 'YouTube' and video['type'] == 'Trailer'), None)
    return {**data, 'poster_url': poster_url, 'trailer_url': trailer_url}

def fetch_genres(): 
    return {g['id']: g['name'] for g in fetch_data(f"https://api.themoviedb.org/3/genre/movie/list?api_key={API_KEY}").get('genres', [])}

def fetch_movies(genre_id, endpoint="discover/movie"): 
    return [fetch_movie_details(m['id']) for m in fetch_data(f"https://api.themoviedb.org/3/{endpoint}?api_key={API_KEY}&with_genres={genre_id}").get('results', [])]

st.set_page_config(page_title="Movie Recommender System", layout="wide")
st.markdown("""<style>.reportview-container {background: #1c1c1c;} h1 {color: orange; text-align: center; font-family: "Georgia", serif; font-weight: bold; font-size: 36px;}</style>""", unsafe_allow_html=True)
st.markdown('<p style="font-size: 36px; font-family: \'Georgia\', serif; color: #cc5801; font-weight: bold; text-align: center;">Movie Recommender System Using ML</p>', unsafe_allow_html=True)

@st.cache_data
def load_data(): return pickle.load(open('movie_list.pkl', 'rb')), pickle.load(open('similarity.pkl', 'rb'))

movies, similarity = load_data()

genres = fetch_genres()
genre_names = list(genres.values())
num_cols = 7
genre_rows = st.columns(num_cols)

for i, genre_name in enumerate(genre_names):
    with genre_rows[i % num_cols]:
        if st.button(f'#{genre_name}', key=f'genre_{i}', use_container_width=True):
            genre_id = next(g_id for g_id, name in genres.items() if name == genre_name)
            with st.spinner(f'Fetching {genre_name} movies...'):
                time.sleep(1)
                st.session_state.selected_genre_movies = fetch_movies(genre_id)
                st.session_state.selected_movie = None
                st.session_state.recommendation_mode = 'genre'

selected_movie = st.selectbox("Select a Movie", movies['title'].values)
show_recommendations = st.button("Show Recommendations")

def display_movie_card(movie, cols):
    with cols:
        st.markdown(f'''
            <div style="background: rgba(0, 0, 0, 0.7); border-radius: 12px; padding: 20px; margin: 10px;">
                <img src="{movie['poster_url']}" style="width: 100%; border-radius: 8px;"/>
                <p style="color: white; text-align: center;">{movie['title']}</p>
                <p style="color: #ccc; font-size: 12px;">Release Date: {movie.get('release_date', 'N/A')}</p>
                <p style="color: #FF5722; font-weight: bold;">Rating: {movie.get('vote_average', 'N/A')}</p>
                <p style="color: #bbb; font-size: 14px;">{movie.get('overview', 'Description not available.')}</p>
                <a href="{movie['trailer_url'] or f'https://www.youtube.com/results?search_query={movie["title"]}'}" target="_blank">
                    <button style="background-color: transparent; border: 2px solid #FF0000; border-radius: 5px; padding: 10px 20px; font-size: 14px; color: #FF0000; font-weight: bold;">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/4/42/YouTube_icon_%282013-2017%29.png" style="width: 20px; margin-right: 10px;"/> Watch Trailer
                    </button>
                </a>
            </div>
        ''', unsafe_allow_html=True)

def display_movies(movies, title):
    st.markdown(f'<p style="font-size: 24px; font-family: \"Georgia\", serif; color: #FF4500; text-align: center;">{title}</p>', unsafe_allow_html=True)
    cols = st.columns(5)
    for i, movie in enumerate(movies[:15]):
        display_movie_card(movie, cols[i % 5])

if selected_movie and show_recommendations:
    st.markdown(f'<p style="font-size: 24px; font-family: \"Georgia\", serif; color: #FF4500; text-align: center;">Recommendations for "{selected_movie}"</p>', unsafe_allow_html=True)
    movie_id = movies[movies['title'] == selected_movie].movie_id.iloc[0]
    recommended_movies = fetch_movies(movie_id, endpoint=f"movie/{movie_id}/recommendations")
    display_movies(recommended_movies, 'Recommended Movies')

if 'selected_genre_movies' in st.session_state and st.session_state.recommendation_mode == 'genre':
    display_movies(st.session_state.selected_genre_movies, 'Movies from Selected Genre')
