from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mysql.connector

# 1. initialize fast api application 
app = FastAPI()

# Database Setup
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "Sushmita@9876",
    "database": "talksta"
}

# 2. define data structure 
class MessagePayload(BaseModel):
    sender: str
    receiver: str
    message: str

# 3. POST Endpoint to transmission and saving of private messages
@app.post("/send_message")
def send_message(data: MessagePayload):
    sender_username = data.sender
    receiver_username = data.receiver
    message_text = data.message

    try:
        db_connection = mysql.connector.connect(**db_config)
        my_cursor = db_connection.cursor()

        # Query sender record reference
        my_cursor.execute("SELECT id FROM users WHERE LOWER(username) = LOWER(%s)", (sender_username,))
        sender_res = my_cursor.fetchone()
        
        # Query receiver record reference
        my_cursor.execute("SELECT id FROM users WHERE LOWER(username) = LOWER(%s)", (receiver_username,))
        receiver_res = my_cursor.fetchone()

        # Validation
        if not sender_res or not receiver_res:
            my_cursor.close()
            db_connection.close()
            raise HTTPException(status_code=404, detail="Sender or Receiver not found in database.")

        sender_id = sender_res[0]
        receiver_id = receiver_res[0]

        # Persist transaction payload into the messages data table
        msg_query = "INSERT INTO messages (sender_id, receiver_id, message_text) VALUES (%s, %s, %s)"
        my_cursor.execute(msg_query, (sender_id, receiver_id, message_text))
        db_connection.commit()

        # Terminate database cursor and connection handles
        my_cursor.close()
        db_connection.close()

        return {"status": "success", "message": "Message saved successfully!"}

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database crash: {str(e)}")


# GET Endpoint to retrieve complete historical message exchange logs
@app.get("/get_messages")
def get_messages(sender: str, receiver: str):
    try:
        db_connection = mysql.connector.connect(**db_config)
        # Instantiating cursor as a dictionary format to simplify response mapping
        my_cursor = db_connection.cursor(dictionary=True)

        # Step A: Validate and retrieve primary account identities
        my_cursor.execute("SELECT id FROM users WHERE LOWER(username) = LOWER(%s)", (sender,))
        sender_res = my_cursor.fetchone()
        
        my_cursor.execute("SELECT id FROM users WHERE LOWER(username) = LOWER(%s)", (receiver,))
        receiver_res = my_cursor.fetchone()

        if not sender_res or not receiver_res:
            my_cursor.close()
            db_connection.close()
            raise HTTPException(status_code=404, detail="User accounts not found.")

        sender_id = sender_res['id']
        receiver_id = receiver_res['id']

        # Step B: Extract transactional logs between target entities using relational SQL JOINs
        history_query = """
            SELECT m.message_text, u1.username as sender_name, u2.username as receiver_name 
            FROM messages m
            JOIN users u1 ON m.sender_id = u1.id
            JOIN users u2 ON m.receiver_id = u2.id
            WHERE (m.sender_id = %s AND m.receiver_id = %s)
               OR (m.sender_id = %s AND m.receiver_id = %s)
            ORDER BY m.id ASC
        """
        my_cursor.execute(history_query, (sender_id, receiver_id, receiver_id, sender_id))
        messages_list = my_cursor.fetchall()

        my_cursor.close()
        db_connection.close()

        return {"status": "success", "messages": messages_list}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database retrieval crash: {str(e)}")
    
@app.get("/api/users")
def get_all_users_list():
    try:
        db_connection = mysql.connector.connect(**db_config)
        my_cursor = db_connection.cursor()
        
        # Extract comprehensive roster of system actors
        my_cursor.execute("SELECT username FROM users ORDER BY username ASC")
        users_tuples = my_cursor.fetchall()
        
        # Map matrix array list into flat sequential strings
        usernames = [u[0] for u in users_tuples]
        
        my_cursor.close()
        db_connection.close()
        return {"status": "success", "users": usernames}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))