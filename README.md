# DeliveryBot

##About
This is a simple Reddit bot that alerts users whether or not a specific user has responded to a comment thread or submission.

##Examples
The bot is triggered by comments left on Reddit.

If the user wants to be notified of the response by the OP of the comment they are replying to, they will leave a comment saying "OP_Deliver!" This by default will always make the grandfather comment the original poster, meaning they will be notified when that user responds the the thread.

```
**Example:**
![Alt text](http://i.imgur.com/T0wWmq3.png "Example Image 1")
```

* In the image above, *u/testing_away* is the original poster.
* *u/onemoretest* leaves the "OP_Deliver!" comment, which means he wants to be notified when *u/testing_away* responds to *u/tester_again*.

```
![Alt text](http://i.imgur.com/bixAM6H.png "Example Image 2")
```

* The bot leaves a comment and private messages *u/onemoretest* a confirmation message.
* The bot will PM *u/onemoretest* whenever *u/testing_away* responds to *u/tester_again* or any of their child comments including the bot.
