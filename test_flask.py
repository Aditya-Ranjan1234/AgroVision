from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def hello():
    return "Flask is working!"

if __name__ == '__main__':
    print("Starting test Flask server...")
    app.run(debug=True, host='0.0.0.0', port=5000)
