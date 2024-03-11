from flask import Flask, render_template, request, redirect, url_for, session


import re
import bcrypt


import numpy as np
import pandas as pd

from datetime import datetime

from dotenv import load_dotenv
import os

from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

popular_df = pd.read_pickle('dataset/popular.pkl1')
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
reviews_collection = db['reviews']
books_collection = db['books']

try:
    client.admin.command('ping')
    print("👌👌Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

bookname = 'xy'

def current_user():
    return session.get('username',None)

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


@app.route('/home')     
def home():
    return render_template('index.html')
    user = current_user()
    users1 = users_collection.find_one({'username':user})
    if user:
        return f'Logged in as {users1}'
    else:
        return 'Login failed'
    
@app.route('/add-review', methods = ['GET','POST'])
def addReview():
    username = current_user()
    # user_details = users_collection.find_one({'username':username})
    if request.method == 'POST':
        bookname = request.form['bookname']
        author = request.form['author']
        rating = request.form['user_rating']
        review = request.form['review']

        # print(bookname,author,rating,review,'💀💀💀💀💀💀💀💀💀💀💀💀💀💀💀💀💀💀💀💀💀💀💀💀💀💀💀💀💀💀💀💀')

        userReviewField = reviews_collection.find_one({'username':username, 'bookname':bookname})
        
        if not userReviewField:
            reviews_collection.insert_one({
                'username' : username,
                    'bookname' : bookname,
                    'author': author,
                    'userrating' : int(rating),
                    'review' : review,
                    'date': str(datetime.utcnow())
            })
            userReviewField = reviews_collection.find_one({'username':username})
        
        else:
            
            reviews_collection.update_one(
                {'username':username},
                {'$set' : {
                    'review' : review,
                    'date': str(datetime.utcnow())
                }
                })
            print(reviews_collection.find_one({'username':username}),'😒😒😒😒😒😒😒😒😒')
        return redirect(url_for('showUserReviews'))
    return render_template('review-form.html')


@app.route('/show-user-reviews', methods= ['GET','POST'])
def showUserReviews():
    username = current_user()
    if request.method == 'GET':
        reviews_list = []
        reviews_tuple = reviews_collection.find({'username':username})
        for review in reviews_tuple:
            review_dict = dict(review)
            rating = []
            for i in range(1,review['userrating']+1):
                rating.append(True)
            for i in range(review['userrating']+1,6):
                rating.append(False)
            review_dict['rating'] = rating
            reviews_list.append(review_dict)
        return render_template('show-user-reviews.html',username= username,bookname = bookname,reviews = reviews_list)
    return 'Herl'

            
@app.route('/show-book-reviews/<string:bookname>', methods= ['GET','POST'])
def showBookReviews(bookname):
    username = current_user()
    if request.method == 'GET':
        reviews_tuple = reviews_collection.find({'bookname':bookname})
        reviews_list = []
        for review in reviews_tuple:
            review_dict = dict(review)
            rating = []
            for i in range(1,review['userrating']+1):
                rating.append(True)
            for i in range(review['userrating']+1,6):
                rating.append(False)
            review_dict['rating'] = rating
            reviews_list.append(review_dict)
        return render_template('show-book-reviews.html',username = username,reviews = reviews_list)


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
import math

@app.route('/summary/<int:id>', methods=['GET','POST'])
def summary(id):
        summary_text = popular_df['summary'].values[int(id)]
        bookname = popular_df['Book-Title'].values[int(id)]
        # print(summary_text)
        return render_template('summary.html',summary_text = summary_text,bookname=bookname)

@app.route('/handpicks')
def index():
    return render_template('home.html',
                           B_N = list(popular_df['Book-Title'].values),
                           B_A=list(popular_df['Book-Author'].values),
                           B_I=list(popular_df['Image-URL-M'].values),
                           B_V=list(popular_df['num_ratings'].values),
                           B_R=list(map(lambda x: round(x/2,1),list(popular_df['avg_rating'].values))),
                           B_S=list(popular_df['summary'].values)
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

        # print(data)

        return render_template('recommend.html',data=data)
    except:
        return render_template('recommend.html',data=[])

if __name__ == '__main__':
    app.run(debug=True)