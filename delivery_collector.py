#!/usr/bin/env python

import praw
import config
import time
import sys
import os
import re
import MySQLdb
import pprint

#================================= GLOBALS =====================================

OP_DELIVER = "op_deliver!" #Comment to trigger the bot
SUBREDDITS = 'testingground4bots' #Add/subtract subreddits here

#For private messages
SUBJECT = "Delivery Bot"
BODY = "I will let you know if OP *maybe* delivers."

#Bot posts this comment to whoever posts "OP_Deliver!"
commentMessage = "***Delivery Bot***\n\nI will let you know if OP *maybe* delivers...\n\n***\rIf anyone else wants reminded, copy the permalink of OP's comment/thread and PM it to me!"

#================================= CLASSES =====================================

#Used to connect to the database
class DatabaseConnection():
    db = None
    cur = None

    def __init__(self):
        self.db = MySQLdb.connect(host=config.host, user=config.username, passwd=config.password, db=config.db)
        self.cur = self.db.cursor()

#Used to search for comments, save to database, and confirm comments were found
class CommentSearch():
    database = DatabaseConnection()

    def __init__(self, subreddits, reddit):
        self.reddit = reddit
        self.search_for_comment(subreddits)
        self.database.db.commit()

    #Searches for the "OP_Deliver comment. Calls necessary functions when one is found."
    def search_for_comment(self, subreddits):
        for submission in subreddits:
            submission.comments.replace_more(limit=50)

            for comment in submission.comments.list():
                if comment.body.lower() == OP_DELIVER: #Whatever is in this global variable
                    try:
                        repliedTo = self.check_replied_to(comment.author, comment.parent().parent().id)
                        alreadyRecorded = self.check_database(comment.author, comment.parent().parent().id)

                        if alreadyRecorded == False and repliedTo == False:
                            self.post_to_database(comment.parent().parent().author, comment.author, submission.id, comment.parent().parent().id)
                            self.post_reply(self.reddit, comment)
                            self.send_message(self.reddit, comment)

                    except Exception as e: #Means a there is a top level comment
                        print str(e) + " Top Level comment!"

                        repliedTo = self.check_replied_to(comment.author, comment.parent().id)
                        alreadyRecorded = self.check_database(comment.author, comment.parent().id)

                        if alreadyRecorded == False and repliedTo == False:
                            self.post_to_database(submission.author, comment.author, submission.id, comment.parent().id)
                            self.post_reply(self.reddit, comment)
                            self.send_message(self.reddit, comment)

                elif re.search(r'op_deliver!', comment.body.lower()) and re.search(r'u/', comment.body):
                    extractedUsername = comment.body.split('u/')

                    try:
                        self.reddit.get('/user/'+ extractedUsername[1] +'/overview')
                        alreadyRecorded = self.check_database(comment.author, comment.parent().id)
                        repliedTo = self.check_replied_to(comment.author, comment.parent().id)

                        if alreadyRecorded == False and repliedTo == False:
                            self.post_to_database(extractedUsername[1], comment.author, submission.id, comment.parent().id)
                            self.post_reply(self.reddit, comment)
                            self.send_message(self.reddit, comment)

                    except Exception as e:
                        print str(e)
                        print "Not a valid user."
                        continue

    #Posts information to the Reddit_Threads table in the database
    def post_to_database(self, username, subscriber, thread_id, comment_id):
        self.database.cur.execute("INSERT INTO Reddit_Threads (username, subscriber, thread_id, comment_id) VALUES (%s, %s, %s, %s)", (username, subscriber, thread_id, comment_id))

    #Checks if the database already contains a certain ID. Returns True if it already contains the ID
    def check_database(self, commentAuthor, commentId):
        self.database.cur.execute("SELECT * FROM Reddit_Threads WHERE subscriber = %s and comment_id = %s", (commentAuthor, commentId))

        if self.database.cur.rowcount == 0:
            return False
        else:
            return True

    #Sends confirmation message to a user
    def send_message(self, reddit, comment):
        redditor = praw.models.Redditor(reddit, str(comment.author))
        test = redditor.message(SUBJECT, BODY)
        print("***** Message sent *****")

    #Posts a comment in response to whoever left "OP_Deliver!"
    def post_reply(self, reddit, comment):
        postComment = praw.models.Comment(reddit, comment.id)

        try:
            postComment.reply(commentMessage)
            print 'Comment submission succeeded'
        except Exception as e:
            print str(e)
            print "Will try to post the comment reply again in 1 minute..."
            time.sleep(60)
            database = DatabaseConnection()
            self.post_reply(reddit, comment)

    #Check to see if someone has already been replied to in the database so it doesn't record them again after removing them from the "Reddit_Threads" table.
    def check_replied_to(self, commentAuthor, commentId):
        self.database.cur.execute("SELECT * FROM Replied_To WHERE subscriber = %s and comment_id= %s", (commentAuthor, commentId))

        if self.database.cur.rowcount == 0:
            return False
        else:
            return True

    #Checks if the "OP_Deliver!" comment is a top level comment. Returns true if it is.
    '''def top_level_comment_check(self, comment, submission):
        if comment.parent().author == submission.author and comment.parent().id == submission.id:
            return True

        return False'''

#================================= FUNCTIONS ===================================

#Extracts IDs from a permalink that is private messaged to this bot, records everything in the database
def record_private_messages(author, url, reddit):
    database = DatabaseConnection()

    extractedThreadId = praw.models.Submission.id_from_url(url)
    extractedCommentId = url.split('/')
    commentId = praw.models.Comment(reddit, extractedCommentId[8])

    threadTable = database.cur.execute("SELECT * FROM Reddit_Threads WHERE username = %s and thread_id = %s", (author, extractedThreadId))
    repliedTable = database.cur.execute("SELECT * FROM Replied_To WHERE subscriber = %s and comment_id = %s", (author, commentId))

    if threadTable == 0 and repliedTable == 0:
        try:
            database.cur.execute("INSERT INTO Reddit_Threads (username, subscriber, thread_id, comment_id) VALUES (%s, %s, %s, %s)", (commentId.author, author, extractedThreadId, commentId))
            respond_to_private_message(reddit, author)
        except Exception as e:
            print str(e)

#Sends a PM to the redditor who sent the bot a PM with the permalink
def respond_to_private_message(reddit, author):
    redditor = praw.models.Redditor(reddit, author)
    redditor.message(SUBJECT, BODY)
    print("***** Message sent *****")

#Create the tables if it doesn't already exist
def create_tables():
    connection = DatabaseConnection()
    connection.cur.execute("CREATE TABLE IF NOT EXISTS Reddit_Threads (username varchar(50), subscriber varchar(50), thread_id varchar(10), comment_id varchar(10), PRIMARY KEY (subscriber, comment_id))")
    connection.cur.execute("CREATE TABLE IF NOT EXISTS Replied_To (subscriber varchar(50), thread_id varchar(10), comment_id varchar(10), PRIMARY KEY (subscriber, comment_id))")

#================================= MAIN ========================================

def main():
    reddit = praw.Reddit('bot1')
    create_tables()

    while True:
        subreddits = reddit.subreddit(SUBREDDITS).hot(limit=5)
        CommentSearch(subreddits, reddit)

        #Handle private messages before sleeping
        messages = reddit.inbox.unread()
        for message in messages:
            match = re.match(r'http', message.body)

            if match:
                record_private_messages(message.author, message.body, reddit)
                message.mark_read()

        print "Sleeping for 60 seconds"
        time.sleep(60)

if __name__ == '__main__':
    main()
