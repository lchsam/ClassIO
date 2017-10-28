"""
For sending message, used with subprocess to send
message asynchronously
"""

import time
import sys
import requests
import json


def time_takes_read_message(single_message, words_per_min=252):
    chars_per_min = words_per_min * 5
    chars_per_sec = chars_per_min / 60
    sec_per_char = 1 / chars_per_sec
    return len(single_message.strip()) * sec_per_char


def send_typing_bubble(sender_id, is_typing):
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": PAGE_ACCESS_TOKEN},
                      headers={"Content-Type": "application/json"},
                      data=json.dumps({
                          "recipient": {"id": sender_id},
                          "sender_action": "typing_on" if is_typing else "typing_off"
                      }))


def send_message(sender_id, message_string):
    """Sending response back to the user using facebook graph API"""
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": PAGE_ACCESS_TOKEN},
                      headers={"Content-Type": "application/json"},
                      data=json.dumps({
                          "recipient": {"id": sender_id},
                          "message": {"text": message_string}
                      }))


def send_image(sender_id, image_attachment_id):
    requests.post("https://graph.facebook.com/v2.6/me/messages",
                  params={"access_token": PAGE_ACCESS_TOKEN},
                  headers={"Content-Type": "application/json"},
                  data=json.dumps({
                      "recipient": {"id": sender_id},
                      "message": {
                          "attachment": {
                              "type": "image",
                              "payload": {"attachment_id": image_attachment_id}
                          }
                      }
                  }))


def mark_message_as_seen(sender_id):
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": PAGE_ACCESS_TOKEN},
                      headers={"Content-Type": "application/json"},
                      data=json.dumps({
                          "recipient": {"id": sender_id},
                          "sender_action": "mark_seen"
                      }))

if __name__ == "__main__":
    arguments = sys.argv[1:]
    PAGE_ACCESS_TOKEN = arguments[0]
    sender_id_number = arguments[1]
    message_list = arguments[2:]

    # Compile arguments to easier arguments for images
    while '-image' in message_list:
        index = message_list.index('-image')
        message_list.pop(index)
        img_attachment_id = message_list[index]
        message_list.pop(index)
        message_list.insert(index, 'image:{id}'.format(id=img_attachment_id))

    # print('{} {} {} {}'.format(arguments, PAGE_ACCESS_TOKEN, sender_id_number, message_list))
    mark_message_as_seen(sender_id_number)
    send_typing_bubble(sender_id_number, True)
    last_index = len(message_list) - 1
    time.sleep(time_takes_read_message(message_list[0]) / 10)
    for index, message in enumerate(message_list):
        is_image_id = 'image:' in message
        if not is_image_id:
            send_message(sender_id_number, message)
        if is_image_id:
            send_image(sender_id_number, message[6:])
        if index != last_index:
            send_typing_bubble(sender_id_number, True)
            time.sleep(time_takes_read_message(message))


