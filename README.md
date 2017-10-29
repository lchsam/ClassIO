<p align="center"><img width=45% src="https://github.com/lchsam/ClassIO/blob/master/misc/logo.png"></p>
<p align="center"><img width=25% src="http://forthebadge.com/images/badges/made-with-python.svg"></p>
<h1 align="center">Class I/O</h1>
<br>
A Facebook bot that notifies users when a selected UMass class is open.

Ever experienced needing to change to a different class after the enrollment period? Or maybe at the beginning of a semester?

If you have experienced these, I'm sure you have incidents where you wanted to enroll in a course, but that class you wanted very much was unfortunately full.

This bot can notify students when their course is open for enrollment!

## Bot In Action




#### Currently in Development
- Use dictionary to implement stages in conversation (welcome -> interested -> notify[/ already open class/ nonexistent class]-> interested if n < 2 / (welcomeback if checks are deleted -> welcome if refresh)/ (open class -> welcomeback if notify is done)
- Limit to 2 class check
- Utilize Subprocess
- Delete class checks (stop messages)
- Checker posts back to main app if open class so user can turn it off
- Server_name for flask to pass in to checker to let it know open class
- Delete subprocesses when enrollment period ends (if anything maybe end of semester)
- Type stage
- Manage Seq
