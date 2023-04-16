'''
This is an implementation of a REST API for a chat application backend
Copyright (C) 2023 Timo Aranjo, Meer Abbas, Marcos Lepage, and Talha Naseer

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''


import mysql.connector
from flask import Flask
from flask import request


#This allows us to make REST API calls to Perspective API
import requests

#Perspective API speaks JSON so we need to be able to speak its language
#Our FLASK implementation uses RAW text
import json

#Create a flask application
app = Flask(__name__)

# Establish a connection to the database
db = mysql.connector.connect(


  host="timoiv.com",
  port="3306",
  user="api",
  password="QCYvH5hl",
  database="m908a985"


)

#Perspective API returns float values in the range [0,1] indicating the properties it measured
#from the comments we sent it.
#These thresholds are what we use to determine if a comment is to be rejected or not
perspective_API_Thresholds = {
    'SEVERE_TOXICITY': .5,
    'INSULT': .5,
    'PROFANITY': .5,
    'IDENTITY_ATTACK': .5,
    'THREAT': .5,
    'SEXUALLY_EXPLICIT': .5
}

perspective_API_Key = "AIzaSyBC3tD-SpMmy_uWfVI62alcux91XtyTz5U"
perspective_API_URL = "https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze?key="

class PerspectiveRequest:
    def __init__(self, url, api_Key, comment, thresholds):
        self._url = url
        self._api_Key = api_Key
        self._comment = comment
        self._thresholds = thresholds
        self._scores = {}

    def _process_Dictionary(self, response_Dictionary):
        for key, obj in response_Dictionary['attributeScores'].items():
           if key != 'languages' and key != 'detectedLanguages':
               self._scores[key] = obj['summaryScore']['value']

    def process_Request(self):
        headers = {'Content-Type': 'application/json'}
        
        data = {
            'comment': {'text': self._comment},
            
            'requestedAttributes': {'SEVERE_TOXICITY': {}, 'INSULT': {}, 'PROFANITY': {},
            'IDENTITY_ATTACK': {}, 'THREAT': {}, 'SEXUALLY_EXPLICIT': {}
            },

            'languages': ["en"]
        }
        
        data_Json = json.dumps(data)

        response = requests.post(self._url + self._api_Key, headers=headers, data=data_Json)
        
        if not (response.status_code >= 200 and response.status_code <= 299):
            raise Exception('Perspective API returned a bad status code')
        
        response_Json = response.text
        response_Dictionary = json.loads(response_Json)
        
        self._process_Dictionary(response_Dictionary)

    def passes_Thresholds(self):
        for key, value in self._thresholds.items():
            if (self._scores[key] > value):
                return False
            
        return True

#This takes an array and converts it into a format that we expect from our get request
#Every comment should have no newlines in it but each comment itself should be separated from each other using
#newlines
def convert_Array_To_Return_Body(array):
    #Declares the string we will return
    string = ""
   
    #For each comment, append it an a newline to the end
    for item in array:
        string += item + "\n"
   
    return string

#When we get a 'GET' request on the url ending '/api/retrieve', we do this
#This is what gets us a list of comments stored on the server
@app.route('/api/retrieve', methods=['GET'])
def retrieve():
    #We declare the comment array that we will be returning
    comment_Array = None
    #We grab the index and length 'GET' variables from the HTTP packet
    index = int(request.args.get('index'))
    length = int(request.args.get('length'))
    try:
        #This will fail if the index is out of bounds
        #We need to account for that
        comment_Array = get_comments(index, length)
    except:
        #Return that it was a bad request if the index was out of bounds
        return 'A 400 (Bad Request) error has occurred. This is probably an error having to do with the index chosen', 400
   
    #Convert the array to our format and return it along with an http response code of 200
    return convert_Array_To_Return_Body(comment_Array), 200 

#This is called whenever a 'POST' request is made to the url ending '/api/post'
#Basically a request to make a new comment
@app.route('/api/post', methods=['POST'])
def post():
    #We take the body of the http packet (the comment to be posted), and we add insert it

    comment = request.data.decode('utf-8')
    
    perspectiveRequest = PerspectiveRequest(perspective_API_URL, perspective_API_Key, comment, perspective_API_Thresholds)
    try:
        perspectiveRequest.process_Request()
    except:
        return '', 500
    
    if not perspectiveRequest.passes_Thresholds():
        return 'The comment failed to pass the content filter', 403
    
    insert_comment(comment)
    #Indicate that the server sucessfully processed the data but won't return anything by using a 204
    #http response code
    return '', 204

#This is called whenever a 'GET' request is made to the url ending '/api/length'
#Just returns the length of our table
@app.route('/api/length', methods=['GET'])
def table_Length():
    return str(get_Length()), '200'

def get_Length():
    cursor = db.cursor()
    #Determine the amount of rows in the COMMENTS table
    cursor.execute("SELECT COUNT(*) FROM COMMENTS")

    # Fetch the result
    result = cursor.fetchone()[0]

    # Print the number of entries in the table
    return result

# Define a function to insert a new comment into the COMMENTS table
def insert_comment(comment):
  cursor = db.cursor()

  # Find the next available comment_number
  cursor.execute("SELECT MAX(comment_number) FROM COMMENTS")
  result = cursor.fetchone()

  comment_number = result[0] + 1 if result[0] else 1

  # Insert the comment into the database
  sql = "INSERT INTO COMMENTS (comment_number, comment) VALUES (%s, %s)"

  values = (comment_number, comment.replace("\n", ""))

  cursor.execute(sql, values)
    #execute function will simply just execute the row at the row the cursor is pointing at at that particular time.
  db.commit()

  return comment_number

# Define a function to retrieve a list of comments from the COMMENTS table
def get_comments(comment_number, length):

  cursor = db.cursor()
  # Check if the starting comment_number exists in the table
  cursor.execute("SELECT COUNT(*) FROM COMMENTS WHERE comment_number >= %s", (comment_number,))
  result = cursor.fetchone()

  if result[0] == 0:
    raise ValueError("Starting comment_number does not exist in the table.")


  # Retrieve the requested comments from the database
  sql = "SELECT comment FROM COMMENTS WHERE comment_number >= %s ORDER BY comment_number LIMIT %s"

  values = (comment_number, length)
  cursor.execute(sql, values)
  results = cursor.fetchall()
  
  comments=[]

  for item in results:
    comments.append(item[0])

  return comments

#Make the REST API server listen on all IP's and port 4000
app.run(host='0.0.0.0', port=4000)

