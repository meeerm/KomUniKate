import mysql.connector

# Establish a connection to the database
db = mysql.connector.connect(


  host="mysql.eecs.ku.edu:3306",
  user="m908a985",
  password="iesh9eiM",
  database="m908a985"


)

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
