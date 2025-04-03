from flask import Flask, request, jsonify, Response,render_template
import ollama
import sqlite3
import subprocess
OLLAMA_PATH = r"C:\Users\haris\AppData\Local\Programs\Ollama\ollama.exe"
app = Flask(__name__)

# Initialize database
def init_db():
    conn = sqlite3.connect("chat_history.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS chat (id INTEGER PRIMARY KEY, user TEXT, bot TEXT)''')
    conn.commit()
    conn.close()

init_db()  # Call database setup

# Streaming generator
def generate_response(user_prompt):
    stream = ollama.chat(model="gemma3", messages=[{"role": "user", "content": user_prompt}], stream=True)
    for part in stream:
        yield part["message"]["content"]

# Store chat in DB
def save_to_db(user_msg, bot_msg):
    conn = sqlite3.connect("chat_history.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat (user, bot) VALUES (?, ?)", (user_msg, bot_msg))
    conn.commit()
    conn.close()

@app.route("/")
def home():
    return render_template("index.html")  # Serve frontend

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_prompt = data.get("prompt", "")

    if not user_prompt:
        return jsonify({"error": "No prompt provided"}), 400

    def stream_response():
        response_text = ""
        for chunk in generate_response(user_prompt):
            response_text += chunk
            yield chunk
        save_to_db(user_prompt, response_text)  # Save to DB

    return Response(stream_response(), content_type="text/plain")


@app.route("/history", methods=["GET"])
def get_chat_history():
    conn = sqlite3.connect("chat_history.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chat ORDER BY id DESC")  # Reverse order (latest first)
    history = [{"id": row[0], "user": row[1], "bot": row[2]} for row in cursor.fetchall()]
    conn.close()
    return jsonify(history)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

