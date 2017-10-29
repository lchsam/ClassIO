"""
Facebook bot (ClassI/O) that checks classes if they are open to enroll
Feature checklist:
[ ] Help command
[ ] website bot documentation on commands
[ ] Save all dictionaries to file for backup (in case server shuts down)
"""

import json
import requests
from flask import Flask, request, render_template
import subprocess
from classstatus import ClassStatus
from random import randint


PAGE_ACCESS_TOKEN = 'LOL NOT GIVING YOU MY PAGE ACCESS TOKEN'

VERIFY_TOKEN = 'LOL'

BOT_ID = "YOUR BOT ID FOR FACEBOOK"

HOST = 'HOST IP'

PORT = 100 # Port number

app = Flask(__name__)

# Associate sender id with their stage in conversation
sender_stage_pair = {}  # {STRING: STRING}
# Associate sender id with their running findcheck script
sender_subprocess_list_pair = {}  # {STRING: [SUBPROCESS]}
# Associate command to stage (using a command moves sender id to a different stage)
command_stage_pair = {'runio': 'TypeNumber'}  # {STRING: STRING}
# Associate sender id with message SUBPROCESS
sender_subprocess_message_pair = {}


@app.route('/', methods=['GET'])
def handle_verification():
    if request.args.get('hub.verify_token', '') == VERIFY_TOKEN:
        print("Verified")
        return request.args.get('hub.challenge', '')
    else:
        print("Wrong token")
        return render_template('default.html')


@app.route('/', methods=['POST'])
def handle_message():
    """Handle messages sent by facebook messenger
    to the application"""

    data = request.get_json()

    # data sent that are not JSON will not be processed
    if data is None:
        return "ok"

    # Check to see if JSON data is from findclass module
    if "object" in data and data["object"] == "finder":
        sender_id = data['sender']['id']
        status = data['class']['status']
        # We can guarantee that post request from findclass is sent AFTER
        # sender_id is put in sender_stage_pair, if not, someone is impersonating
        # the request. There are definitely better ways to verify the source
        # of the post request but...
        if sender_id not in sender_stage_pair:
            return "ok"
        if status == ClassStatus.invalid.value:
            send_invalid_input_message(sender_id)
            pop_subprocess_list(sender_id)
            change_stage_back(sender_id)
            return "ok"
        class_name = data['class']['name']
        if sender_stage_pair[sender_id] == 'Running' or sender_stage_pair[sender_id] == 'Open':
            is_full = status == ClassStatus.full.value
            # For debugging
            # print('{}-------{}-------{}'.format(sender_id, class_name,
            #                                     is_full))
            send_status_change_message(sender_id,
                                       class_name,
                                       is_full)
            if not is_full:
                sender_stage_pair[sender_id] = 'Open'
                return "ok"
            sender_stage_pair[sender_id] = 'Running'
            return "ok"
        if status == ClassStatus.open.value:
            send_already_open_message(sender_id, class_name)
            pop_subprocess_list(sender_id)
            change_stage_back(sender_id)
            return "ok"
        if status == ClassStatus.waitlist.value:
            send_waitlist_message(sender_id, class_name)
            pop_subprocess_list(sender_id)
            change_stage_back(sender_id)
            return "ok"
        sender_stage_pair[sender_id] = "Running"
        running_stage(sender_id, class_name)
        return "ok"

    # Check to see if JSON data is from facebook
    if "object" in data and data["object"] == "page":
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                if messaging_event.get("message"):

                    sender_id = messaging_event["sender"]["id"]
                    # recipient_id = messaging_event["recipient"]["id"]
                    # If POST request is not related to user messages,
                    # Ignore it
                    if sender_id == BOT_ID:
                        return "ok"

                    message_text = "Non-text message"
                    if messaging_event["message"].get("text"):
                        message_text = messaging_event["message"]["text"]

                    # For debugging
                    # print(sender_id + str('-------') + message_text)
                    process_message(sender_id, message_text)

    return "ok"


def process_message(sender_id, message):
    """Given a facebook sender id and message, process it accordingly"""
    if message == 'del':
        pop_subprocess_list(sender_id)
        # For debugging
        # print('{}-Sub:----{}'.format(sender_id, sender_subprocess_list_pair))
        sender_stage_pair[sender_id] = "TypeNumber"
        return
    if message.lower() in command_stage_pair and sender_stage_pair[sender_id] == "Running":
        sender_stage_pair[sender_id] = command_stage_pair[message.lower()]
        send_change_stage_message(sender_id, message.lower())
        return
    if sender_id not in sender_stage_pair:
        sender_stage_pair[sender_id] = "Welcome"
        send_welcome_message(sender_id)
        return
    if sender_stage_pair[sender_id] == "Welcome":
        sender_stage_pair[sender_id] = "TypeNumber"
        interested_stage(sender_id)
        return
    if sender_stage_pair[sender_id] == "TypeNumber":
        if message is None:
            return
        message = "".join(message.split())
        if bad_number_input(message):
            send_bad_input_message(sender_id)
            return
        send_receive_number_message(sender_id)
        class_number = message
        cmd = 'exec python findclass.py {host} {port} {class_num} {sender_id}'.format(
            host=HOST,
            port=PORT,
            class_num=class_number,
            sender_id=sender_id
        )
        # A subprocess is used to do asynchronous stuff
        findclass_subprocess = subprocess.Popen(cmd, shell=True)
        subprocess_list = sender_subprocess_list_pair.get(sender_id, [])
        subprocess_list.append(findclass_subprocess)
        sender_subprocess_list_pair[sender_id] = subprocess_list
        sender_stage_pair[sender_id] = "CheckNumber"
        return
    if sender_stage_pair[sender_id] == "CheckNumber":
        send_checking_number_message(sender_id)
        return
    if sender_stage_pair[sender_id] == "Running":
        send_running_message(sender_id)
    if sender_stage_pair[sender_id] == "Open":
        pop_subprocess_list(sender_id)  # Does not work with multiple subprocess
        sender_stage_pair[sender_id] = "Running"
        send_got_class_message(sender_id)


def send_welcome_message(sender_id):
    message = "Hi! \nMy name is ClassI/O. I notify you when a full " \
              "class, lab or discussion at UMass (Amherst) is open to enroll!\n" \
              "If interested, respond with anything :)"
    send_message_response(sender_id, message)


def interested_stage(sender_id):
    image_id = '783441551834741'
    message = "I'm glad you're interested!\n" \
              "Please type in the class number " \
              "of a course you would like to receive notifications for.\n" \
              "I provided an image below showing where to find the class number!\n" \
              "-image\n{image}\n" \
              "For example, for the above class, I would type in:\n" \
              "39321".format(image)
    send_message_response(sender_id, message)


def running_stage(sender_id, class_name):
    message = "Great! I'll notify you when '" + class_name + "' is open :)"
    send_message_response(sender_id, message)


def send_invalid_input_message(sender_id):
    message = "This class doesn't seem to exist\n" \
              "Please try again :("
    message2 = "Sorry, I cannot seem to find this class\n" \
               "Maybe try again?"
    message3 = "Hmm, can't seem to find this class\n" \
               "I can certain try again if you provide a another class number :)"
    messages = [message, message2, message3]
    if randint(1, 50) == randint(1, 25):
        messages = ["You can try typing help for more information :P"]
    send_message_response(sender_id, messages[randint(0, len(messages)-1)])


def send_already_open_message(sender_id, class_name):
    message = "I went on Spire and it seems the class, '" + class_name + "' is already open!\n" \
              "If this is the class you want to enroll in, get on Spire right now!\n" \
              "If not, you can try again with another class number"
    send_message_response(sender_id, message)


def send_waitlist_message(sender_id, class_name):
    message = "Looks like '" + class_name + "' lets you enroll in its waitlist\n" \
              "I think being on their waitlist is better than using me ;)\n" \
              "If you have other classes you would like to get notifications for,\n" \
              "I can still help!"
    send_message_response(sender_id, message)


def send_status_change_message(sender_id, class_name, is_full):
    message = "Quick! '{}' is open!\n" \
              "Grab it before anyone gets it!\n" \
              "Say something like got it so that I know that you got the class :)".format(class_name)
    if is_full:
        message = "Oh, it seems like '{}' is full again :/".format(class_name)
    send_message_response(sender_id, message)


def send_bad_input_message(sender_id):
    message = "It doesn't seem like the number you replied with is " \
              "an actual class number.\n" \
              "Sorry, try again :("
    send_message_response(sender_id, message)


def send_running_message(sender_id):
    message = "I'll definitely notify you when your class is open to enroll!\n" \
              "Please be patient :)"
    message2 = "I can actually do a bit more than you think, type help to see more"
    message3 = "Visit this site, {website} for more info about me :P".format(website="")
    message4 = "Please report any bugs over at this email: {email}".format(email='')
    messages = [message, message2, message3, message4]
    send_message_response(sender_id, messages[randint(0, len(messages)-1)])


def send_checking_number_message(sender_id):
    message = "I'm still checking Spire hehe\n" \
              "Gimme a sec"
    send_message_response(sender_id, message)


def send_change_stage_message(sender_id, stage_command):
    stage = command_stage_pair[stage_command]
    send_message_response(sender_id, 'Woah! Who told you about this hidden feature?!\n Anyway, enjoy :)')
    if stage == 'TypeNumber':
        send_message_response(sender_id, 'Please type in another class number ;)')


def send_got_class_message(sender_id):
    message = "Yay! You got it! :D\nYou can type in another class number if you need to find another class."
    send_message_response(sender_id, message)


def pop_subprocess_list(sender_id):
    if sender_id not in sender_subprocess_list_pair:
        return
    if not sender_subprocess_list_pair[sender_id]:
        return
    if sender_subprocess_list_pair[sender_id][-1].poll() is None:
        sender_subprocess_list_pair[sender_id][-1].kill()
    sender_subprocess_list_pair[sender_id].pop()


def change_stage_back(sender_id):
    is_running = sender_subprocess_list_pair.get(sender_id, [])
    sender_stage_pair[sender_id] = "Running" if is_running else "TypeNumber"


def bad_number_input(message):
    from re import search
    if not len(message) == 5:
        return True
    if search('[^0-9]', message) is not None:
        return True
    return False


def send_receive_number_message(sender_id):
    message = "Oki, I'll be right with you after seeing if the class is full first :)"
    send_message_response(sender_id, message)


def send_message_response(sender_id, message_text):
    """Send message response with subprocess allowing asynchronous message sending
     and facebook 200 http communication"""
    sentence_delimiter = "\n"
    messages = message_text.split(sentence_delimiter)
    cmd = ['python', 'sendmessage.py', PAGE_ACCESS_TOKEN, sender_id]
    cmd += messages
    # Using a list of arguments, with shell=True, shell runs python independent of the arguments
    message_subprocess = subprocess.Popen(cmd)
    if sender_id in sender_subprocess_message_pair:
        sender_subprocess_message_pair[sender_id].kill()
    sender_subprocess_message_pair[sender_id] = message_subprocess


if __name__ == "__main__":
    app.run(host=HOST, port=PORT)
