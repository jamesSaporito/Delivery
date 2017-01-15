#!/usr/bin/env python

#===============================================================================
#***** This program will only work for one subreddit at a time *****************
#===============================================================================

import praw
import time
import sys
import os
import re
import MySQLdb

#================================= GLOBALS =====================================

OP_DELIVER = "op_deliver!"
SUBREDDIT = 'testingground4bots'
SUBJECT = "Delivery Bot"
BODY = "I will let you know if OP *maybe* delivers."
reply_message = "I will let you know if OP *maybe* delivers!"
list_of_redditors = list() #A list of classes "RedditorsSubscribed"
reddit_threads = list()

#DATABASE CONNECTION

#db = MySQLdb.connect(host="", user="", passwd="", db="") #Fill this in with relevant data
db.autocommit(True)
cur = db.cursor()

#================================= CLASSES =====================================

#Contains the redditors username and their comment ID
class RedditorsSubscribed():
    def __init__(self, username, comment_id):
        self.username = username
        self.comment_id = comment_id

#Contains the submission ID of a reddit thread and the original posters username(author)
class RedditThreadData():
    def __init__(self, submission_id, author):
        self.submission_id = submission_id
        self.author = author

#================================= FUNCTIONS ===================================

#Searches threads and finds comments that match with the OP_DELIVER variable and appends the class RedditorsSubscribed instance to "list_of_redditors"
def search_for_comment(subreddit):
    for submission in subreddit:
        result = check_database(submission.id)

        if result == False: #If the database doesn't contain the ID
            submission.comments.replace_more(limit=4)

            for comment in submission.comments.list():
                if comment.body.lower() == OP_DELIVER:

                    already_responded_to = check_replied_to(comment.author, comment.parent().id)
                    if already_responded_to == False:
                        list_of_redditors.append(RedditorsSubscribed(comment.author, comment.id))
                        reddit_threads.append(RedditThreadData(submission.id, submission.author)) #MAKE TABLE FOR THIS DATA

                        result = check_database(submission.id)
                        if result == False:
                            cur.execute("INSERT INTO Reddit_Threads (username, subscriber, thread_id, comment_id) VALUES (%s, %s, %s, %s)", (comment.parent().author, comment.author, submission.id, comment.parent().id))

#Sends message to a user
def send_message(reddit):
    for person in list_of_redditors:    #Take for loop out of here eventually
        redditor = praw.models.Redditor(reddit, str(person.username))
        test = redditor.message(SUBJECT, BODY)
        print("***** Message sent *****")

#Replies to a comment that contains the string of the variable OP_DELIVER
def post_reply(reddit, redditor_to_reply_to):
    comment = praw.models.Comment(reddit, redditor_to_reply_to.comment_id)

    try:
        #comment.reply(reply_message)
        print 'Comment succeeded...'
    except:
        print "Will try to post the comment reply again in 1 minute..."
        time.sleep(60)
        post_reply(reddit, redditor_to_reply_to)

#Checks if the database already contains a certain ID. Returns TRUE if it already contains the ID
def check_database(submission): #Rename this to "check_reddit_threads"
    cur.execute("SELECT * FROM Reddit_Threads WHERE thread_id = %s", [submission])

    if cur.rowcount == 0:
        return False
    else:
        return True

#Check to see if someone has already been replied to in the database
def check_replied_to(comment_author, comment_id):
    cur.execute("SELECT * FROM Replied_To WHERE subscriber = %s and comment_id= %s", (comment_author, comment_id))

    if cur.rowcount == 0:
        return False
    else:
        return True

#Extracts IDs from a permalink that is private messaged to this bot, records everything in the database
def record_private_messages(author, url, reddit):
    extracted_thread_id = praw.models.Submission.id_from_url(url)
    extracted_comment_id = url.split('/')
    comment_id = praw.models.Comment(reddit, extracted_comment_id[8])

    thread_table = cur.execute("SELECT * FROM Reddit_Threads WHERE username = %s and thread_id = %s", (author, extracted_thread_id))
    replied_table = cur.execute("SELECT * FROM Replied_To WHERE subscriber = %s and comment_id = %s", (author, comment_id))

    if thread_table == 0 and replied_table == 0:
        cur.execute("INSERT INTO Reddit_Threads (username, subscriber, thread_id, comment_id) VALUES (%s, %s, %s, %s)", (comment_id.author, author, extracted_thread_id, comment_id))

def respond_to_private_message(reddit, author):
    redditor = praw.models.Redditor(reddit, author)
    redditor.message(SUBJECT, BODY)
    print("***** Message sent *****")


#================================= MAIN ========================================

def main():
    reddit = praw.Reddit('bot1')

    #Create the table if it doesn't already exist
    cur.execute("CREATE TABLE IF NOT EXISTS Reddit_Threads (username varchar(50), subscriber varchar(50), thread_id varchar(10), comment_id varchar(10), PRIMARY KEY (subscriber))")
    cur.execute("CREATE TABLE IF NOT EXISTS Replied_To (subscriber varchar(50), thread_id varchar(10), comment_id varchar(10))")

    while True:
        subreddit = reddit.subreddit(SUBREDDIT).new(limit=5)
        search_for_comment(subreddit)

        #Sends a PM to people who want to be notified
        for number in range(len(list_of_redditors)):
            post_reply(reddit, list_of_redditors[number])
            print "post_reply is commented out. Comment not posted"

        send_message(reddit)

        list_of_redditors[:] = [] #Empty the list once everything is written to the database

        #To prevent spamming Reddit, once someone has already posted "OP_Deliver!", other users
        #who want to be notified will be asked to copy the permalink from that comment and private message
        #it to this bot.

        #Handle private messages before sleeping
        messages = reddit.inbox.unread()
        if messages == 0:
            print "No new messages"
        else:
            for message in messages:
                record_private_messages(message.author, message.body, reddit)
                respond_to_private_message(reddit, message.author)
                message.mark_read()

        print "Sleeping for 5 seconds"
        time.sleep(5)

if __name__ == '__main__':
    main()
