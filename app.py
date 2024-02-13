from flask import Flask, render_template, request, redirect, url_for, session
import re
import bcrypt


import numpy as np
import pandas as pd


from dotenv import load_dotenv
import os

from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

popular_df = pd.read_pickle('dataset/popular.pkl')
pt = pd.read_pickle('dataset/pt.pkl')
books = pd.read_pickle('dataset/books.pkl')
similarity_scores = pd.read_pickle('dataset/similarity_scores.pkl')

app = Flask(__name__)

load_dotenv()
SECRET_KEY = os.environ['SECRET_KEY']
MONGODB_URI = os.environ['MONGODB_URI']

app.secret_key = SECRET_KEY

client = MongoClient(MONGODB_URI)
db = client.get_database('User_records')
users_collection = db['users']

try:
    client.admin.command('ping')
    print("👌👌Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

def is_mongo_connected():
    try:
        # Check if the connection is alive
        return client.is_mongoclient_alive()
    except Exception as e:
        print("failed")

@app.route('/')
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        password_encoded = password.encode('utf-8')

        user = users_collection.find_one({'email':email})
        if user and bcrypt.checkpw(password_encoded,user['password']):
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            return 'Invalid login credentials'
    return render_template('login.html')
    

@app.route('/signin', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        password_encoded = password.encode('utf-8')
        hashed_password = bcrypt.hashpw(password_encoded, bcrypt.gensalt())

        if not users_collection.find_one({'email': email}):
            users_collection.insert_one({
                'fullname': fullname, 
                'username': username, 
                'email' : email,
                'password': hashed_password
                })
            return redirect(url_for('login'))
        else:
            return 'User already exists with the given email'
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