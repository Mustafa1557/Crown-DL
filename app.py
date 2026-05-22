from flask import Flask, request, jsonify
import google.generativeai as genai
import os

app = Flask(__name__)

# API KEY
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")


@app.route("/")
def home():
    return "AI Bot Running 24/7 🚀"


@app.route("/ai", methods=["POST"])
def ai():
    try:
        data = request.get_json()

        message = data["message"]

        response = model.generate_content(message)

        return jsonify({
            "success": True,
            "reply": response.text
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
