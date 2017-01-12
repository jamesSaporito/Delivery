#!/usr/bin/env python

#===============================================================================
#***** This program will only work for one subreddit at a time *****************
#***** At the moment it can only handle one "delivery" at a time per thread ****
#===============================================================================

import praw
import time
import sys
import os
import re
import MySQLdb

#================================= GLOBALS =====================================

OP_DELIVER = "op_deliver!"
SUBJECT = "Delivery Bot"
BODY = "I will let you know if OP *maybe* delivers."
reply_message = "I will let you know if OP *maybe* delivers."
list_of_redditors = list() #Should be a list of classes "RedditorsSubscribed"
reddit_threads = list()

#DATABASE CONNECTION

db = MySQLdb.connect(host="", user="", passwd="", db="") #Fill this in with relevant data
db.autocommit(True)
cur = db.cursor()

#================================= CLASSES =====================================

#Contains the redditors username and their comment ID
class RedditorsSubscribed():
    #username_and_comment_id = dict()

    def __init__(self, username, comment_id):
        self.username = username
        self.comment_id = comment_id
        #self.username_and_comment_id[username] = comment_id

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
                    list_of_redditors.append(RedditorsSubscribed(comment.author, comment.id))
                    reddit_threads.append(RedditThreadData(submission.id, submission.author)) #MAKE TABLE FOR THIS DATA

                    result = check_database(submission.id)
                    if result == False:
                        cur.execute("INSERT INTO Reddit_Threads (username, id) VALUES (%s, %s)", (submission.author, submission.id))


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
        comment.reply(reply_message)
        print 'Comment succeeded...'
    except:
        print "Will try to post the comment reply again in 10 minutes..."
        time.sleep(600)
        post_reply(reddit, redditor_to_reply_to)

#Checks if the database already contains a certain ID. Returns TRUE if it already contains the ID
def check_database(submission):
    cur.execute("SELECT * FROM Reddit_Threads WHERE id = %s", [submission])

    if cur.rowcount == 0:
        return False
    else:
        return True

#Extracts IDs from a permalink that is private messaged to this bot, records everything in the database
def record_private_messages(author, url, reddit):
    extracted_thread_id = praw.models.Submission.id_from_url(url)
    #extracted_comment_id_author = url.split('/')
    #username = praw.models.Comment(reddit, extracted_comment_id_author[8])

    cur.execute("SELECT * FROM Reddit_Threads WHERE username = %s and id = %s", (author, extracted_thread_id))

    if cur.rowcount == 0:
        cur.execute("INSERT INTO Reddit_Threads (username, id) VALUES (%s, %s)", (author, extracted_thread_id))

    print "comment id author :" + str(author)
    #print "thread id : " + extracted_thread_id
    #print "comment id : " + str(test)

def respond_to_private_message(reddit, author):
    redditor = praw.models.Redditor(reddit, author)
    redditor.message(SUBJECT, BODY)
    print("***** Message sent *****")


#================================= MAIN ========================================

#TO DO LIST:
#1) Must have a table in database of people already replied to?
#2) Handle private messages

def main():
    reddit = praw.Reddit('bot1')

    #Create the table if it doesn't already exist
    cur.execute("CREATE TABLE IF NOT EXISTS Reddit_Threads (username varchar(50), id varchar(10))")
    #cur.execute("DROP TABLE Reddit_Threads") #For testing purposes only
    #sys.exit()

    while True:
        subreddit = reddit.subreddit('testingground4bots').new(limit=5)
        search_for_comment(subreddit)

        #Sends a PM to people who want to be notified
        for number in range(len(list_of_redditors)):
            post_reply(reddit, list_of_redditors[number])

        send_message(reddit)

        list_of_redditors[:] = [] #Empty the list once everything is written to the database

        '''
        To prevent spamming Reddit, once someone has already posted "OP_Deliver!", other users
        who want to be notified will copy the permalink from that comment and private message
        it to this bot.
        '''
        #Handle private messages before sleeping
        messages = reddit.inbox.unread()

        for message in messages:
            record_private_messages(message.author, message.body, reddit)
            respond_to_private_message(reddit, message.author)
            message.mark_read()

        print "Sleeping for 60 seconds"
        time.sleep(60)

if __name__ == '__main__':
    main()
