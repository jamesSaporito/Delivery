#!/usr/bin/env python

import praw
import time
import sys
import MySQLdb

#================================= GLOBALS =====================================

SUBJECT = "Delivery!!!"
BODY = "OP *may* have delivered! Here is the link to the thread: "

#DATABASE CONNECTION

#db = MySQLdb.connect(host="", user="", passwd="", db="") #Fill this in with relevant data
db.autocommit(True)
cur = db.cursor()

#================================= FUNCTIONS ===================================

#Searches recorded threads to see if OP has delivered or not
def search_for_delivery(reddit):
    cur.execute("SELECT DISTINCT username, comment_id FROM Reddit_Threads")
    rows = cur.fetchall()   #Gets data from SQL statement above and goes through it one by one

    #data[0] is the username and data[1] is the comment ID
    for data in rows:
        try:
            comments = reddit.comment(id=data[1])
            comments.refresh()
            for comment in comments.replies.list():
                if comment.author == data[0]:
                    find_subscribers(reddit)
                else:
                    continue
        except:
            submission = reddit.submission(id=data[1])
            for comment in submission.comments.list():
                if comment.author == data[0]:
                    find_subscribers(reddit)
                else:
                    continue


def find_subscribers(reddit):
    cur.execute("SELECT DISTINCT subscriber, thread_id, comment_id FROM Reddit_Threads")
    rows = cur.fetchall()
    for data in rows:
        url = reddit.submission(id=data[1])

        if check_replied_to(data[0], data[2]) == False:
            message_op_delivered(reddit, url.shortlink, data[0])
            update_databases(reddit, data[0], data[1], data[2])

#Sends messages that OP delivered
def message_op_delivered(reddit, shortlink, subscriber): #Select all repeats of the id if reply is found
    redditor = praw.models.Redditor(reddit, subscriber)
    test = redditor.message(SUBJECT, BODY + shortlink)
    print("***** Message sent *****")

def update_databases(reddit, subscriber, thread_id, comment_id):
    cur.execute("INSERT INTO Replied_To (subscriber, thread_id, comment_id) VALUES (%s, %s, %s)", (subscriber, thread_id, comment_id)) #insert this info into the Responded_To table
    cur.execute("DELETE FROM Reddit_Threads WHERE subscriber = %s and comment_id = %s", (subscriber, comment_id))

#Check to see if someone has already been replied to in the database
def check_replied_to(comment_author, thread_id):
    cur.execute("SELECT * FROM Replied_To WHERE subscriber = %s and comment_id = %s", (comment_author, thread_id))

    if cur.rowcount == 0:
        return False
    else:
        return True

#================================= MAIN ========================================

#TO DO:
#1) If a thread is deleted, remove the submission id from the file and the redditors who wanted to be alerted.

def main():
    reddit = praw.Reddit('bot1')
    cur.execute("CREATE TABLE IF NOT EXISTS Replied_To (subscriber varchar(50), thread_id varchar(10), comment_id varchar(10))")

    while True:
        search_for_delivery(reddit)

        print "Sleeping for 5 seconds"
        time.sleep(5)

if __name__ == '__main__':
    main()
