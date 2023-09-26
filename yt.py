import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import numpy as np
import seaborn as sns
import pymongo as pg 
from sqlalchemy import create_engine
from datetime import datetime
import time
import pymysql
import isodate
pymysql.install_as_MySQLdb()
import matplotlib.pyplot as plt

st.set_page_config(page_title="Youtube Harvesting", layout="wide", initial_sidebar_state="auto", menu_items=None)
#st.title(":red[YOUTUBE DATA] :red[HARVESTING] and :red[WAREHOUSING] ▶️ ")

#uploads
api_key = 'AIzaSyBcuPuQy680CetRiIaXgfIY_yCgkd_JWvA' #from user
youtube = build('youtube','v3',developerKey= api_key)

st.subheader("Uploading data to MongoDB Database")


#Function to retrieve channel stats
# args - channel_id

#@st.cache_data
def get_channel_stats(channel_id):
    channel_table = []
    response = youtube.channels().list(part = 'snippet,contentDetails,statistics',id= channel_id).execute()
    
    for item in response['items']:
        data = dict(
                    channel_id = item['id'],
                    channel_name = item['snippet']['title'],
                    channel_description = item['snippet']["description"],
                    channel_subscribers= item['statistics']['subscriberCount'],
                    channel_views = item['statistics']['viewCount'],
                    total_videos = item['statistics']['videoCount'],
                    playlist_id = item['contentDetails']['relatedPlaylists']['uploads'])
                
        channel_table.append(data)
    
    return channel_table



# # Function to get playlist_id

#@st.cache_data
def get_playlist_data(df):
    playlist_ids = []
     
    for i in df["playlist_id"]:
        playlist_ids.append(i)

    return playlist_ids

# Function to get video_ids

#@st.cache_data
def get_video_ids(playlist_id):
    video_id = []

    for i in playlist_id:
        next_page_token = None
        more_pages = True

        while more_pages:
            request = youtube.playlistItems().list(
                        part = 'contentDetails',
                        playlistId = i,
                        maxResults = 50,
                        pageToken = next_page_token)
            response = request.execute()
            
            for j in response["items"]:
                video_id.append(j["contentDetails"]["videoId"])
        
            next_page_token = response.get("nextPageToken")
            if next_page_token is None:
                more_pages = False
    return video_id

# Function to get video_details

#@st.cache_data
def get_video_details(video_id):

    all_video_stats = []
   

    for i in range(0,len(video_id),50):
        
        request = youtube.videos().list(
                  part="snippet,contentDetails,statistics",
                  id = ",".join(video_id[i:i+50]))
        response = request.execute()
        
        
        for video in response["items"]:
            published_dates = video["snippet"]["publishedAt"]
            parsed_dates = datetime.strptime(published_dates,'%Y-%m-%dT%H:%M:%SZ')
            format_date = parsed_dates.strftime('%Y-%m-%d')
            duration = video["contentDetails"]["duration"]
            Duration = isodate.parse_duration(duration)
            v_duration = Duration.total_seconds()
            

            videos = dict(video_id = video["id"],
                          channel_name = video['snippet']['channelTitle'],
                          channel_id = video["snippet"]["channelId"],
                          video_name = video["snippet"]["title"],
                          video_duration =v_duration ,
                          video_published_date = format_date ,
                          video_views = video["statistics"].get("viewCount",0),
                          video_likes = video["statistics"].get("likeCount",0),
                          video_comments= video["statistics"].get("commentCount",0))
            all_video_stats.append(videos)

    return (all_video_stats)

# # Function to get comments

#@st.cache_data
def get_comments(video_id):
    comments_data= []
    try:
        next_page_token = None
        for i in video_id:
            while True:
                request = youtube.commentThreads().list(
                    part = "snippet,replies",
                    videoId = i,
                    textFormat="plainText",
                    maxResults = 100,
                    pageToken=next_page_token)
                response = request.execute()
                

                for item in response["items"]:
                    published_date= item["snippet"]["topLevelComment"]["snippet"]["publishedAt"]
                    parsed_dates = datetime.strptime(published_date,'%Y-%m-%dT%H:%M:%SZ')
                    format_date = parsed_dates.strftime('%Y-%m-%d')
                    

                    comments = dict(comment_id = item["id"],
                                    video_id = item["snippet"]["videoId"],
                                    comment_text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"],
                                    comment_author = item["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"],
                                    comment_published_date = format_date)
                    comments_data.append(comments) 
                
                next_page_token = response.get('nextPageToken')
                if next_page_token is None:
                    break       
    except Exception as e:
        print("Error retrieving comments",str(e))          
            
    return comments_data

# user giving input
channel_id = []
#UCmapkf4A5883lT90j86WXFg

option = st.number_input('**Enter the number of channels**', value=1, min_value=1,max_value=10)
for i in range(option):
        channel_id.append(st.text_input("**Enter the ChannelId**", key=i))

submit = st.button("Get Channel details")

# # Connection to MongoDB

mongodb_local = pg.MongoClient("mongodb://localhost:27017")

#create database

youtube_db = mongodb_local["youtube"]

#collection creation

channel_coll = youtube_db['channel_data']
video_coll = youtube_db['video_data']
comment_coll = youtube_db['comments_data']

if submit:
    if channel_id:
        channel_details = get_channel_stats(channel_id)
        df = pd.DataFrame(channel_details) 
        playlist_id = get_playlist_data(df)
        video_id = get_video_ids(playlist_id)
        video_details = get_video_details(video_id)
        get_comment_data = get_comments(video_id)

        with st.spinner('loading..... '):
            time.sleep(5)
            st.success('Done, Data successfully Fetched')

            if channel_details:
                channel_coll.insert_many(channel_details)
            if video_details:
                video_coll.insert_many(video_details)
            if get_comment_data:
                comment_coll.insert_many(get_comment_data)

        with st.spinner('loading..... '):
            time.sleep(5)
            st.success('Done!, Data Successfully Uploaded')
    
    
#Fetch the data from MongoDB:

#Select channel names for user input from MondoDB

def channel_names():   
    ch_name = []
    for i in youtube_db.channel_data.find():
        ch_name.append(i['channel_name'])
    return ch_name

st.subheader("Inserting data into MySQL...........")

user_input =st.multiselect("Select the channel to be inserted into MySQL Tables",options = channel_names())

submit_next = st.button("Upload the data into MySQL")

#Fetch the channel_details

if submit_next:
    
    with st.spinner('loading... '):
        
        def get_channel_details(user_input):
            query = {"channel_name":{"$in":list(user_input)}}
            projection = {"_id":0,"channel_id":1,"channel_name":1,"channel_views":1,"channel_subscribers":1,"total_videos":1,"playlist_id":1}
            x = channel_coll.find(query,projection)
            channel_table = pd.DataFrame(list(x))
            return channel_table

        channel_data = get_channel_details(user_input)
        
        #Fetch the Video details:
         
        def get_video_details(channel_list):
            query = {"channel_id":{"$in":channel_list}}
            projection = {"_id":0,"video_id":1,"channel_id":1,"channel_name":1,"video_name":1,"video_published_date":1,"video_views":1,"video_likes":1,"video_comments":1,"video_duration":1}
            x = video_coll.find(query,projection)
            video_table = pd.DataFrame(list(x))
            return video_table
        video_data = get_video_details(channel_id)

        #Fetch the comment_details
        def get_comment_details(video_ids):
            query = {"video_id":{"$in":video_ids}}
            projection = {"_id":0,"comment_id":1,"video_id":1,"comment_text":1,"comment_author":1,"comment_published_date":1}
            x = comment_coll.find(query,projection)
            comment_table = pd.DataFrame(list(x))
            return comment_table
        
        #Fetch video_ids from mongoDb

        video_ids = video_coll.distinct("video_id")
        
        comment_data = get_comment_details(video_ids)
        
        mongodb_local.close()
        
        # MYSQL CONNECTION

        mydb = pymysql.connect(
            host="localhost",
            port = 3306,
            user="root",
            password="W@2915djkq#",
            database="youtube_harvesting")

        mycursor = mydb.cursor()

        #create an SQLAlchemy engine
        
        engine = create_engine('mysql+pymysql://root:W@2915djkq#@localhost/youtube_harvesting')

        #Inserting Channel data into the table

        try:
            channel_data.to_sql('channel_data', con=engine, if_exists='append', index=False, method='multi')
            print("Data inserted successfully")
        except Exception as e:
            if 'Duplicate entry' in str(e):
                print("Duplicate data found. Ignoring duplicate entries.")
            else:
                print("Error occured inserting Channel data:", e)

    
        #Inserting Video data into the table 

        try:
            video_data.to_sql('video_data', con=engine, if_exists='append', index=False, method='multi')
            print("Data inserted successfully")
        except Exception as e: 
            if 'Duplicate entry' in str(e):
                print("Duplicate data found. Ignoring duplicate entries.")
            else:
                print("Error occured inserting Video data:", e)
        st.success("Data Uploaded Successfully")
        engine.dispose()

st.subheader("Select any questions ?")


#MYSQL Database connection

mydb = pymysql.connect(
    host="localhost",
    port = 3306,
    user="root",
    password="W@2915djkq#",
    database="youtube_harvesting")

mycursor = mydb.cursor()

questions = st.selectbox("Select any questions given below:",
['Click the question that you would like to query',
'1. What are the names of all the videos and their corresponding channels?',
'2. Which channels have the most number of videos, and how many videos do they have?',
'3. What are the top 10 most viewed videos and their respective channels?',
'4. How many comments were made on each video, and what are their corresponding video names?',
'5. Which videos have the highest number of likes, and what are their corresponding channel names?',
'6. What is the total number of likes for each video, and what are their corresponding video names?',
'7. What is the total number of views for each channel, and what are their corresponding channel names?',
'8. What are the names of all the channels that have published videos in the year 2022?',
'9. What is the average duration of all videos in each channel, and what are their corresponding channel names?',
'10. Which videos have the highest number of comments, and what are their corresponding channel names?'])


#store the queries

if questions == '1. What are the names of all the videos and their corresponding channels?':
    query = "select distinct channel_name as Channel_name , video_name as Video_name from video_data order by cast(video_name as unsigned) asc;"
    table = pd.read_sql(query,mydb)
    st.write(table)
    st.success('Success!.. Move to next Questions')
elif questions == '2. Which channels have the most number of videos, and how many videos do they have?':
    query = "select distinct channel_name as Channel_name,count(video_name) as Most_Number_of_Videos from video_data group by channel_name order by cast(Most_Number_of_Videos as unsigned) desc;"
    mycursor.execute(query)
    result = mycursor.fetchall()
    table = pd.DataFrame(result, columns=['Channel_name', 'Number_of_Videos']).reset_index(drop=True)
    table.index += 1
    st.dataframe(table)
    st.success('Success!.. Move to next Questions')
elif questions == '3. What are the top 10 most viewed videos and their respective channels?':
                a = pd.read_sql("SELECT channel_Name FROM channel_data", mydb)
                channels_id = []
                for i in range(len(a)):
                    channels_id.append(a.loc[i].values[0])

                ans3 = pd.DataFrame()
                for each_channel in channels_id:
                    Q3 = f"SELECT * FROM video_data WHERE channel_name='{each_channel}' ORDER BY video_views DESC LIMIT 10"
                    ans3 = pd.concat([ans3, pd.read_sql(Q3, mydb)], ignore_index=False)
                st.write(ans3[['video_name', 'channel_name', 'video_views']])
                st.success('Success!.. Move to next Questions')
elif questions == '4. How many comments were made on each video, and what are their corresponding video names?':
    query = "select distinct channel_name as Channel_name , video_name as Video_name , video_comments as Comments_count from video_data order by cast(channel_name as unsigned) desc;"
    table = pd.read_sql(query,mydb)
    st.write(table)
    st.success('Success!.. Move to next Questions')
elif questions == '5. Which videos have the highest number of likes, and what are their corresponding channel names?':
    query = "select distinct channel_name as Channel_name,video_name as Video_name,video_likes as Number_of_likes from video_data order by cast(video_likes as unsigned) desc limit 10;"
    table = pd.read_sql(query,mydb)
    st.write(table)
    st.success('Success!.. Move to next Questions')
elif questions == '6. What is the total number of likes for each video, and what are their corresponding video names?':
    query = "select distinct video_name as Video_name,video_likes as Like_count from video_data order by cast(Like_count as unsigned) desc;"
    table = pd.read_sql(query,mydb)
    st.write(table)
    st.success('Success!.. Move to next Questions')
elif questions == '7. What is the total number of views for each channel, and what are their corresponding channel names?':
    query = " select distinct channel_name as Channel_name , channel_views as total_number_of_views from channel_data order by cast(channel_views as unsigned) desc;"
    table = pd.read_sql(query,mydb)
    st.write(table)
    st.success('Success!.. Move to next Questions')
elif questions == '8. What are the names of all the channels that have published videos in the year 2022?':
    query = "select distinct channel_name as Channel_name , year(video_published_date) as published_year from video_data where year(video_published_date) = 2022;"
    table = pd.read_sql(query,mydb)
    st.write(table)
    st.success('Success!.. Move to next Questions')
elif questions == '9. What is the average duration of all videos in each channel, and what are their corresponding channel names?':
    query ="SELECT channel_name AS Channel_Name,AVG(video_duration) AS Average_duration FROM video_data GROUP BY channel_name ORDER BY AVG(video_duration) DESC;"
    table = pd.read_sql(query,mydb)
    st.write(table)
    st.success('Success!.. Move to next Questions')
elif questions =='10. Which videos have the highest number of comments, and what are their corresponding channel names?':
    query = "select distinct channel_name as Channel_name , video_name as Video_name, video_comments as No_of_comments from video_data order by cast(video_comments as unsigned) desc limit 10;"
    table = pd.read_sql(query,mydb)
    st.write(table)
    st.success('Successfully Done') 
    st.write('Thanks for giving me this oppurtunity 😇') 

mycursor.close()
mydb.close()