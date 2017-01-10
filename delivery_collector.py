#!/usr/bin/env python

#==============================================================================#
#***** This program will only work for one subreddit at a time ****************#
#***** At the moment it can only handle one "delivery" at a time per thread ***#
#***** If the program ends, everything is lost ********************************#
#==============================================================================#

import praw
import time
import sys
import mmap
import os

#================================= GLOBALS =====================================

OP_DELIVER = "op_deliver!"
SUBJECT = "Delivery Bot"
BODY = "I will let you know if OP Delivers."
reply_message = "Testing"
list_of_redditors = list() #Should be a list of classes "RedditorsSubscribed"
reddit_threads = list()
reddit_threads_file = open("Reddit_Threads.txt", "a+") #Contains submission ID and the author(original poster of the thread)
redditors_subscribed_file = open("Redditors_Subscribed_File.txt", "a+") #Contains the commentors username and the comment ID.


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
    #author_and_id = dict()

    def __init__(self, submission_id, author):
        self.submission_id = submission_id
        self.author = author
        #self.author_and_id[submission_id] = author

#================================= FUNCTIONS ===================================

#Searches threads and finds comments that match with the OP_DELIVER variable and appends the class RedditorsSubscribed instance to "list_of_redditors"
def search_for_comment(subreddit):
    for submission in subreddit:
        result = check_file(submission.id, reddit_threads_file)

        if result == False: #If the file doesn't contain the ID
            submission.comments.replace_more(limit=4)

            for comment in submission.comments.list():
                if comment.body.lower() == OP_DELIVER:
                    list_of_redditors.append(RedditorsSubscribed(comment.author, comment.id))
                    reddit_threads.append(RedditThreadData(submission.id, submission.author))

                    result = check_file(submission.id, reddit_threads_file)
                    if result == False:
                        data = str(submission.author) + ' ' + str(submission.id)
                        write_to_file(reddit_threads_file, data)

#Sends message to a user.
def send_message(reddit):
    for people in list_of_redditors:
        redditor = praw.models.Redditor(reddit, str(people.username))
        test = redditor.message(SUBJECT, BODY)
        print("***** Message sent *****")
    return

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

#Checks if a file already contains a certain ID. Returns TRUE if it already contains the ID.
def check_file(submission, current_file):   #Pass the file even though it's global to determine with file to check
    current_file.seek(0, 0)
    if os.stat(current_file.name).st_size != 0:  #Checks if the file is empty or not
        s = mmap.mmap(current_file.fileno(), 0, access=mmap.ACCESS_READ)

        if s.find(submission) == -1:
            return False
        else:
            return True
    else:
        return False

#Writes to the file. Fix with error checking. #Pass the file even though it's global to determine with file to write to
def write_to_file(current_file, data):
    current_file.write(data + '\n')

#================================= MAIN ========================================

def main():
    reddit = praw.Reddit('bot1')

    while True:
        subreddit = reddit.subreddit('testingground4bots').new(limit=5)

        redditors_subscribed_file = open("redditors_subscribed_File.txt", "a+")
        reddit_threads_file = open("Reddit_Threads.txt", "a+")

        search_for_comment(subreddit)

        for number in range(len(list_of_redditors)):
            #Check for posts replied to
            post_reply(reddit, list_of_redditors[number])

            data = str(list_of_redditors[number].username) + ' ' + str(list_of_redditors[number].comment_id) #Each data set gets one line in the file
            write_to_file(redditors_subscribed_file, data)

        send_message(reddit)

        list_of_redditors[:] = [] #Empty the list once everything is written to the file.

        redditors_subscribed_file.close()
        reddit_threads_file.close()

        print "Sleeping for 60 seconds"
        time.sleep(60)

if __name__ == '__main__':
    main()
