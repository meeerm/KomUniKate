import mysql.connector
from flask import Flask

#Create a flask application
app = Flask(__name__)

# Establish a connection to the database
db = mysql.connector.connect(


  host="mysql.eecs.ku.edu:3306",
  user="m908a985",
  password="iesh9eiM",
  database="m908a985"


)


#This takes an array and converts it into a format that we expect from our get request
#Every comment should have no newlines in it but each comment itself should be separated from each other using
#newlines
def convert_Array_To_Return_Body(array):
    #Declares the string we will return
    string = ""
   
    #For each comment, append it an a newline to the end
    for item in array:
        string += array + "\n"
   
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
        return 'A 400 (Bad Request) error has occurred. This is probably an error having to do with the index        chosen', 400
   
    #Convert the array to our format and return it along with an http response code of 200
    return convert_Array_To_Return_Body(comment_Array), 200
   

#This is called whenever a 'POST' request is made to the url ending '/api/post'
#Basically a request to make a new comment
@app.route('/api/post', methods=['POST'])
def post():
    #We take the body of the http packet (the comment to be posted), and we add insert it
    insert_comment(request.data)
    #Indicate that the server sucessfully processed the data but won't return anything by using a 204
    #http response code
    return '', 204


# Define a function to insert a new comment into the COMMENTS table
def insert_comment(comment):
  cursor = db.cursor()

  # Find the next available comment_number
  cursor.execute("SELECT MAX(comment_number) FROM COMMENTS")
  result = cursor.fetchone()

  comment_number = result[0] + 1 if result[0] else 1

  # Insert the comment into the database
  sql = "INSERT INTO COMMENTS (comment_number, comment) VALUES (%s, %s)"

  values = (comment_number, comment.replace('\n', ' '))

  cursor.execute(sql, values)
    #execute function will simply just execute the row at the row the cursor is pointing at at that particular time.
  db.commit()

  return comment_number

# Define a function to retrieve a list of comments from the COMMENTS table
def get_comments(comment_number, length):

  cursor = db.cursor()
  # Check if the starting comment_number exists in the table
  cursor.execute("SELECT COUNT(*) FROM COMMENTS WHERE comment_number >= %s", (comment_number))
  result = cursor.fetchone()


  if result[0] == 0:
    raise ValueError("Starting comment_number does not exist in the table.")


  # Retrieve the requested comments from the database
  sql = "SELECT comment FROM COMMENTS WHERE comment_number >= %s ORDER BY comment_number LIMIT %s"

  values = (comment_number, length)
  cursor.execute(sql, values)
  results = cursor.fetchall()
  comments = [row[0] for row in result]
  return comments

#Make the REST API server listen on all IP's and port 4000
app.run(host='0.0.0.0', port=4000)

