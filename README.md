<p align="center"><img width=40% src="https://github.com/lchsam/ClassIO/blob/master/misc/logo.png"></p>
<p align="center"><img style="max-width:80%;" src="http://forthebadge.com/images/badges/made-with-python.svg"></p>
<h1 align="center">Class I/O</h1>
<br>
A Facebook bot that notifies users when a selected UMass class is open.

Ever experienced needing to change to a different class after the enrollment period? Or maybe at the beginning of a semester?

If you have experienced these, I'm sure you have incidents where you wanted to enroll in a course, but that class you wanted very much was unfortunately full.

This bot can notify students when their course is open for enrollment!

## Bot In Action
<h3 align="center">Welcoming Message</h3>
<p align="center"><img style="max-width:80%;" src="https://github.com/lchsam/ClassIO/blob/master/misc/entry.gif"></p>
<br>
<h3 align="center">Recognizing already open classes</h3>
<p align="center"><img style="max-width:80%;" src="https://github.com/lchsam/ClassIO/blob/master/misc/openalready.gif"></p>
<br>
<h3 align="center">Recognize full classes and notify accordingly</h3>
<p align="center"> Fully implemented, GIF is WIP </p>

## How it works
![alt text](https://github.com/lchsam/ClassIO/blob/master/misc/diagram.png "Diagram")
```ngrok-fbbpoy.py ```is responsible for handling incoming messages from facebook. ```sendmessage.py``` is directed by ```ngrok-fbbot.py``` to send messages back to Facebook. ```findclass.py``` is a module that identifies validity of a class number. If it is valid, the module then determines if this class is full or open.

## Dependencies
### Selenium 
Used in ```findclass.py``` to determine class status.
### Flask
Used in ```ngrok-fbbot.py``` to communicate with Facebook
### Requests
Used in ```findclass.py```, ```ngrok-fbbot.py``` and ```sendmessage.py``` to send posts requests.
