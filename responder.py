#!/usr/bin/env python

import praw
import config
import time
import sys
import MySQLdb
import pprint

#================================= GLOBALS =====================================

SUBJECT = "Delivery!!!"
BODY = "OP *may* have delivered! Here is the link to the thread: "

#================================= CLASSES =====================================

#Used to connect to the database
class DatabaseConnection():
    db = None
    cur = None

    def __init__(self):
        self.db = MySQLdb.connect(host=config.host, user=config.username, passwd=config.password, db=config.db)
        self.cur = self.db.cursor()

class DeliverySearch():
    database = DatabaseConnection()

    def __init__(self, reddit):
        self.reddit = reddit
        self.search_for_delivery()
        self.database.db.commit()

    #Searches recorded threads to see if OP has delivered or not
    def search_for_delivery(self):
        self.database.cur.execute("SELECT DISTINCT username, comment_id FROM Reddit_Threads")
        rows = self.database.cur.fetchall()

        for data in rows:
            try:
                comments = self.reddit.comment(id=data[1])
                comments.refresh()

                for comment in comments.replies.list():
                    if comment.author == data[0]:
                        self.find_subscribers(self.reddit)
                    else:
                        continue
            except Exception as e:
                print str(e) + " *Top level comment detected*"

                submission = self.reddit.submission(id=data[1])
                print submission.id

                for comment in submission.comments:
                    if comment.author == data[0]:
                        self.find_subscribers(self.reddit)
                    else:
                        continue

    #Gets all of the subscribers when a delivery is found. data[0] = subscriber, data[1] = thread_id, data[2] = comment_id
    def find_subscribers(self, reddit):
        self.database.cur.execute("SELECT DISTINCT subscriber, thread_id, comment_id FROM Reddit_Threads")
        rows = self.database.cur.fetchall()
        for data in rows:
            url = self.reddit.submission(id=data[1])

            if self.check_replied_to(data[0], data[2]) == False:
                self.message_op_delivered(reddit, url.shortlink, data[0])
                self.update_databases(reddit, data[0], data[1], data[2])

    #Sends messages that OP maybe delivered
    def message_op_delivered(self, reddit, shortlink, subscriber):
        redditor = praw.models.Redditor(reddit, subscriber)
        redditor.message(SUBJECT, BODY + shortlink)
        print("***** Message sent *****")

    #Removes data from the "Reddit_Threads" table and puts it into the "Replied_To" table
    def update_databases(self, reddit, subscriber, thread_id, comment_id):
        self.database.cur.execute("DELETE FROM Reddit_Threads WHERE subscriber = %s and comment_id = %s", (subscriber, comment_id))
        self.database.cur.execute("INSERT INTO Replied_To (subscriber, thread_id, comment_id) VALUES (%s, %s, %s)", (subscriber, thread_id, comment_id)) #insert this info into the Responded_To table

    #Check to see if someone has already been replied to in the database
    def check_replied_to(self, comment_author, thread_id):
        self.database.cur.execute("SELECT * FROM Replied_To WHERE subscriber = %s and comment_id = %s", (comment_author, thread_id))

        if self.database.cur.rowcount == 0:
            return False
        else:
            return True


#Create the tables if they don't already exist
def create_tables():
    connection = DatabaseConnection()
    connection.cur.execute("CREATE TABLE IF NOT EXISTS Reddit_Threads (username varchar(50), subscriber varchar(50), thread_id varchar(10), comment_id varchar(10), PRIMARY KEY (subscriber, comment_id));")
    connection.cur.execute("CREATE TABLE IF NOT EXISTS Replied_To (subscriber varchar(50), thread_id varchar(10), comment_id varchar(10), PRIMARY KEY (subscriber, comment_id))")

#================================= MAIN ========================================

def main():
    reddit = praw.Reddit('bot1')
    create_tables()

    while True:
        DeliverySearch(reddit)

        print "Sleeping for 60 seconds"
        time.sleep(60)

if __name__ == '__main__':
    main()
