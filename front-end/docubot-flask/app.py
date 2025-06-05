from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow CORS for all domains (for local React dev)

@app.route("/llm", methods=["POST"])
def llm_response():
    data = request.get_json()
    user_message = data.get("message", "")

    # Just a sample, echoing back
    bot_reply = f"Sample response from Flask API. You said: {user_message}"

    return jsonify({"reply": bot_reply})

if __name__ == "__main__":
    app.run(debug=True, port=5000)