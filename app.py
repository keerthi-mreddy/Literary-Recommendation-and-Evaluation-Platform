from flask import Flask,render_template,request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import os
import pandas as pd
import numpy as np


from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

popular_df = pd.read_pickle('dataset/popular.pkl')
pt = pd.read_pickle('dataset/pt.pkl')
books = pd.read_pickle('dataset/books.pkl')
similarity_scores = pd.read_pickle('dataset/similarity_scores.pkl')

app = Flask(__name__)
 
app.secret_key = os.environ['SECRET_KEY']

client = MongoClient(os.environ['MONGODB_URI'])
db = client.get_database('User_records')
users_collection = db['users']

def is_mongo_connected():
    try:
        # Check if the connection is alive
        return client.is_mongoclient_alive()
    except Exception as e:
        print(f"Error checking MongoDB connection: {e}")
        return False

@app.route('/')
@app.route('/login')
def home():
    if is_mongo_connected():
        print('Connected to MongoDB')
        return render_template('login.html')
    else:
        return 'Not connected to MongoDB'
    

@app.route('/signin')
def home1():
    return render_template('signin.html')

@app.route('/handpicks')
def index():
    return render_template('home.html',
                           B_N = list(popular_df['Book-Title'].values),
                           B_A=list(popular_df['Book-Author'].values),
                           B_I=list(popular_df['Image-URL-M'].values),
                           B_V=list(popular_df['num_ratings'].values),
                           B_R=list(map(lambda x:round(x,1),list(popular_df['avg_rating'].values)))
                           )

@app.route('/recommend')
def recommend_ui():
    return render_template('recommend.html')

@app.route('/recommend_books',methods=['post'])
def recommend():
    try:
        user_input = request.form.get('user_input')
        print(user_input)
        index = np.where(pt.index == user_input)[0][0]
        similar_items = sorted(list(enumerate(similarity_scores[index])), key=lambda x: x[1], reverse=True)[1:5]

        data = []
        for i in similar_items:
            item = []
            temp_df = books[books['Book-Title'] == pt.index[i[0]]]
            item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Title'].values))
            item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Author'].values))
            item.extend(list(temp_df.drop_duplicates('Book-Title')['Image-URL-M'].values))

            data.append(item)
        if len(data) == 0:
            return render_template('recommend0.html')

        print(data)

        return render_template('recommend.html',data=data)
    except:
        return render_template('recommend.html',data=[])

if __name__ == '__main__':
    app.run(debug=True)