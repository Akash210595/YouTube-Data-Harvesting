Project aims to develop a user-friendly Streamlit application that utilizes the Google API to extract information on a YouTube channel, stores it in a MongoDB database, migrates it to a SQL data warehouse, and enables users to search for channel details and join tables to view data in the Streamlit app.
PROBLEM STATEMENT:
	
 	The problem statement is to create a Streamlit application that allows users to access and analyze data from multiple YouTube channels.

OVERVIEW:
	
 	An app that extracts data from youtube for the user provided input using Google API that saves retrieved information into MongoDB and transform and save into MYSQl and finally displays the details to the end user in tabular format. 

WORKFLOW:
	
 	Create a Google account and connect it to YouTube API to extract data’s. 
  	Create an API-key to extract data’s like channels, videos, comments from any YouTube channels. 
	With a click of button in stream lit using stream lit API store the extracted data’s into MongoDB Lake. 
 	By converting unstructured data’s into Data Frame and migrating it to MYSQL.
  	Using queries on MYSQL we fetch data’s by given user input and present them into table format using Stream lit application.
