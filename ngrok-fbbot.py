"""
Facebook bot (ClassI/O) that checks classes if they are open to enroll
Feature checklist:
[ ] Help command
[ ] website bot documentation on commands
[ ] Save all dictionaries to file for backup (in case server shuts down)
"""
from flask import Flask, request, render_template

HOST = '127.0.0.1'

PORT = 5000

app = Flask(__name__)

@app.route('/', methods=['GET'])
def handle_verification():
    if request.args.get('hub.verify_token', '') == VERIFY_TOKEN:
        print("Verified")
        return request.args.get('hub.challenge', '')
    else:
        print("Wrong token")
        return render_template('default.html')


if __name__ == "__main__":
    app.run(host=HOST, port=PORT)