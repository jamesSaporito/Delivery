# DeliveryBot

##About
This is a bot that alerts users of Reddit whether or not a specific user has responded to a comment thread or submission. Since there is no real way to determine if the original poster actually delivered or not, besides actually reading the comment, it private messages users when another user responds to a certain thread, which is determined by the comment.

##Examples
A user leaves the comment "OP_Deliver!" to be notified if the original poster of the grandfather comment replies to that thread.

**Example 1:**
![Alt text](http://i.imgur.com/T0wWmq3.png "Example Image 1")

* In the image above, *u/testing_away* is the original poster.
* In this scenario, *u/tester_again* asked *u/testing_away* something they would need to answer, or 'deliver.'
* *u/onemoretest* leaves the "OP_Deliver!" comment, which means he wants to be notified when *u/testing_away* responds to *u/tester_again*.

![Alt text](http://i.imgur.com/bixAM6H.png "Example Image 2")

* The bot leaves a comment and private messages *u/onemoretest* a confirmation message.
* The bot will private message *u/onemoretest* whenever *u/testing_away* responds to *u/tester_again* or any of their child comments including the bot.


**Example 2:**
* Another scenario is if a user wants to be notified if the Redditor they are replying to responds.
* The user will post "OP_Deliver! u/username" and can target any Redditor as the original poster.
* In this case, the original poster would respond to the "OP_Deliver!" comment for the notification to be delivered.


If it's a top level comment (responding to the actual post), then the submission poster will be considered the original poster.
