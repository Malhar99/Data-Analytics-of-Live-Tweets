# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

# Python modules
import os, logging 

# Flask modules
from flask               import render_template, request, url_for, redirect, send_from_directory
from flask_login         import login_user, logout_user, current_user, login_required
from werkzeug.exceptions import HTTPException, NotFound, abort
from datetime import time
# App modules
from app        import app, lm, db, bc
from app.models import User
from app.forms  import LoginForm, RegisterForm
from app.analysis_live_tweets import TweetAnalyzer,TwitterClient

# Twitter modules
from tweepy import API
from tweepy import Cursor
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream

from textblob import TextBlob

import numpy as np
import pandas as pd
import re
import json

# provide login manager with load_user callback
@lm.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Logout user
@app.route('/logout.html')
def logout():
    logout_user()
    return redirect(url_for('index'))

# Register a new user
@app.route('/register.html', methods=['GET', 'POST'])
def register():
    
    # declare the Registration Form
    form = RegisterForm(request.form)

    msg = None

    if request.method == 'GET': 

        return render_template('layouts/auth-default.html',
                                content=render_template( 'pages/register.html', form=form, msg=msg ) )

    # check if both http method is POST and form is valid on submit
    if form.validate_on_submit():

        # assign form data to variables
        username = request.form.get('username', '', type=str)
        password = request.form.get('password', '', type=str) 
        email    = request.form.get('email'   , '', type=str) 

        # filter User out of database through username
        user = User.query.filter_by(user=username).first()

        # filter User out of database through username
        user_by_email = User.query.filter_by(email=email).first()

        if user or user_by_email:
            msg = 'User exists!'
        
        else:         

            pw_hash = password #bc.generate_password_hash(password)

            user = User(username, email, pw_hash)

            user.save()

            msg = 'User created, please <a href="' + url_for('login') + '">login</a>'     

    else:
        msg = 'Input error'     

    return render_template('layouts/auth-default.html',
                            content=render_template( 'pages/register.html', form=form, msg=msg ) )

# Authenticate user
@app.route('/login.html', methods=['GET', 'POST'])
def login():
    
    # Declare the login form
    form = LoginForm(request.form)

    # Flask message injected into the page, in case of any errors
    msg = None

    # check if both http method is POST and form is valid on submit
    if form.validate_on_submit():

        # assign form data to variables
        username = request.form.get('username', '', type=str)
        password = request.form.get('password', '', type=str) 

        # filter User out of database through username
        user = User.query.filter_by(user=username).first()

        if user:
            
            #if bc.check_password_hash(user.password, password):
            if user.password == password:
                login_user(user)
                return redirect(url_for('index'))
            else:
                msg = "Wrong password. Please try again."
        else:
            msg = "Unknown user"

    return render_template('layouts/auth-default.html',
                            content=render_template( 'pages/login.html', form=form, msg=msg ) )

# App main route + generic routing
@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path>')
def index(path):

    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    content = None
    sname = current_user.user
    twitter_client = TwitterClient()
    tweet_analyzer = TweetAnalyzer()
    positive=0
    negative=0
    neutral=0
    api = twitter_client.get_twitter_client_api()
    """
    Limitation:
        Analysis upto First 200 tweets only
    """
    tweets = api.user_timeline(screen_name=sname , count=200)
    df = tweet_analyzer.tweets_to_data_frame(tweets)
    ###find the term we can analysis ###
    #print(dir(tweets[0]))
    ### count tweets according to its Sentiments ###
    Name = df['Name'][0]
    Number_of_Followers =  np.max(df['Followers'])
    Number_of_Followings = np.max(df['Followings'])
    # Get the number of likes for the most liked tweet:
    MaxLikes = np.max(df['Likes'])

    # # Get the number of retweets for the most retweeted tweet:
    MaxRetweets = np.max(df['Retweets'])
    df['Sentiment'] = np.array([tweet_analyzer.analyze_sentiment(tweet) for tweet in df['Tweets']])
    for senti in df['Sentiment']:
        if(senti == "Positive"):
            positive+=1
        elif(senti == "Controversial"):
            negative+=1
        else:
            neutral+=1
    Positive_tweets = df["Sentiment"] == "Positive"
    PTweets=df[Positive_tweets]["Tweets"].tolist()
    PLikes=df[Positive_tweets]["Likes"].tolist()
    PRetweets=df[Positive_tweets]["Retweets"].tolist()
    lenp=len(PTweets)
    Controversial_tweets = df["Sentiment"] == "Controversial"
    CTweets=df[Controversial_tweets]["Tweets"].tolist()
    CLikes=df[Controversial_tweets]["Likes"].tolist()
    CRetweets=df[Controversial_tweets]["Retweets"].tolist()
    lenc=len(CTweets)
    Neutral_tweets = df["Sentiment"] == "Neutral"
    NTweets=df[Neutral_tweets]["Tweets"].tolist()
    NLikes=df[Neutral_tweets]["Likes"].tolist()
    NRetweets=df[Neutral_tweets]["Retweets"].tolist()
    lenn=len(NTweets)
    ### arrange the data according to sentiments ###

    ### plot Graphs for the Data Anaylsis ###

    ### Sentiment Analysis Chart
    slices = [positive,neutral,negative]
    

    ### likes Analysis Chart
    xdlikes=df['Date']
    ylikes=df['Likes'].values

    ### Retweets Analysis Chart
    xdretweet=df['Date']
    yretweet=df['Retweets'].values                                

    ### Sources used for Tweets
    svalues = df['Source'].value_counts().keys().tolist()
    scounts = df['Source'].value_counts().tolist()

    ### Hashtags used in Tweets
    df.drop(df[df.Hashtags == ''].index, inplace=True)
    hvalues = df['Hashtags'].value_counts().keys().tolist()
    hcounts = df['Hashtags'].value_counts().tolist()
    
    # Name=Name,Number_of_Followers=Number_of_Followers,Number_of_Followings=Number_of_Followings,MaxLikes=MaxLikes,MaxRetweets=MaxRetweets
    # legend = 'Monthly Data'
    # labels = ["January", "February", "March", "April", "May", "June", "July", "August"]
    # values = [10, 9, 8, 7, 6, 4, 7, 8]
    
    try:
       
        return render_template('layouts/default.html',
                                content=render_template( 'pages/'+path,Name=Name,Number_of_Followers=Number_of_Followers,Number_of_Followings=Number_of_Followings,MaxLikes=MaxLikes,MaxRetweets=MaxRetweets,slices=slices,svalues=svalues,scounts=scounts,xdlikes=xdlikes,ylikes=ylikes,xdretweet=xdretweet,yretweet=yretweet,hvalues=hvalues,hcounts=hcounts,PTweet=PTweets,PLikes=PLikes,PRetweets=PRetweets,lenp=lenp,CTweet=CTweets,CLikes=PLikes,CRetweets=CRetweets,lenc=lenc,NTweet=NTweets,NLikes=NLikes,NRetweets=NRetweets,lenn=lenn))
    except:
        
        return render_template('layouts/auth-default.html',
                                content=render_template( 'pages/404.html' ) )

# Return sitemap 
@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'sitemap.xml')
