#!/usr/bin/env python

import praw
import config
import time
import sys
import os
import re
import MySQLdb

#================================= GLOBALS =====================================

OP_DELIVER = "op_deliver!"
SUBREDDITS = 'AMA' #Add subreddits here
SUBJECT = "Delivery Bot"
BODY = "I will let you know if OP *maybe* delivers."
commentMessage = "**Delivery Bot**\n\nI will let you know if OP *maybe* delivers...\n\n***\rIf anyone else wants reminded, copy the permalink of the comment or thread and PM it to me!"

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

    #Searches threads and finds comments that match with the OP_DELIVER variable and appends the class RedditorsSubscribed instance to "list_of_redditors"
    def search_for_comment(self, subreddits):
        for submission in subreddits:
            #result = self.check_database(submission.id) #What if there are multiple threads in a submission that want delivered.....

            #if result == False: #If the database doesn't contain the ID
            submission.comments.replace_more(limit=50)

            for comment in submission.comments.list():
                if comment.body.lower() == OP_DELIVER: #Whatever is in this global variable
                    if comment.parent().parent() == submission.id: #old one is comment.parent().id
                        response = self.check_replied_to(comment.author, comment.id)
                    else:
                        response = self.check_replied_to(comment.author, comment.parent().id)

                    #print comment.parent().parent()
                    #print submission.id
                    #print comment.parent()
                    if response == False:
                        result = self.check_database(comment.author, comment.parent().id)
                        '''
                        print result
                        print comment.author
                        print comment.id
                        print comment.parent()
                        print comment.parent().parent()
                        print comment.parent().author
                        '''
                        if result == False:
                            self.database.cur.execute("INSERT INTO Reddit_Threads (username, subscriber, thread_id, comment_id) VALUES (%s, %s, %s, %s)", (comment.parent().author, comment.author, submission.id, comment.parent().id))
                            self.post_reply(self.reddit, comment)
                            self.send_message(self.reddit, comment)
                elif re.search(r'op_deliver!', comment.body.lower()) and re.search(r'u/', comment.body): #match = re.match(r'http', message.body)
                    extractedUsername = comment.body.split('u/')

                    try:
                        self.reddit.get('/user/'+ extractedUsername[1] +'/overview')
                        result = self.check_database(comment.author, comment.parent().id)
                        response = self.check_replied_to(comment.author, comment.parent().id)

                        #print comment.author
                        #print comment.parent().id
                        if result == False and response == False:
                            self.database.cur.execute("INSERT INTO Reddit_Threads (username, subscriber, thread_id, comment_id) VALUES (%s, %s, %s, %s)", (extractedUsername[1], comment.author, submission.id, comment.parent().id))
                            self.post_reply(self.reddit, comment)
                            self.send_message(self.reddit, comment)

                    except Exception as e:
                        print str(e)
                        print "Not a valid user."
                        continue
                    #Check if it's a valid user
                    #Check if it's in the database with the associated commentId


    #Checks if the database already contains a certain ID. Returns TRUE if it already contains the ID
    def check_database(self, commentAuthor, commentId):
        self.database.cur.execute("SELECT * FROM Reddit_Threads WHERE subscriber = %s and comment_id = %s", (commentAuthor, commentId))

        if self.database.cur.rowcount == 0:
            return False
        else:
            return True

    #Sends message to a user
    def send_message(self, reddit, comment):
        redditor = praw.models.Redditor(reddit, str(comment.author))
        test = redditor.message(SUBJECT, BODY)
        print("***** Message sent *****")

    #Replies to a comment that contains the string of the variable OP_DELIVER
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

    #Check to see if someone has already been replied to in the database
    def check_replied_to(self, commentAuthor, commentId):
        self.database.cur.execute("SELECT * FROM Replied_To WHERE subscriber = %s and comment_id= %s", (commentAuthor, commentId))

        if self.database.cur.rowcount == 0:
            return False
        else:
            return True

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

        print "Sleeping for 30 seconds"
        time.sleep(30)

if __name__ == '__main__':
    main()
