#!/usr/bin/env python

#===============================================================================
#***** This program will only work for one subreddit at a time *******
#***** At the moment it can only handle one "delivery" per thread ****
#===============================================================================

import praw
import time
import sys
import mmap
import os

#================================= GLOBALS =====================================

OP_DELIVER = "test"
SUBJECT = "Delivery Bot"
BODY = "I will let you know if OP Delivers."
reply_message = "Test"
list_of_redditors = list() #Should be a list of classes "RedditorsSubscribed"
reddit_threads = list()
reddit_threads_file = open("Reddit_Threads.txt", "a+") # "Contains thread IDs"
#comments_file = open("Comments_IDs.txt", "a+")

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
        result = check_file(submission.id, reddit_threads_file)

        if result != True: #If the file doesn't contain the ID
            submission.comments.replace_more(limit=4)
            for comment in submission.comments.list():
                if comment.body.lower() == OP_DELIVER:
                    list_of_redditors.append(RedditorsSubscribed(comment.author, comment.id))
                    reddit_threads.append(RedditThreadData(submission.id, submission.author))

                    result = check_file(submission.id, reddit_threads_file)
                    if result == False:
                        write_to_file(reddit_threads_file, submission.id)

#Sends message to a user.
def send_message(reddit):
    for people in list_of_redditors:
        redditor = praw.models.Redditor(reddit, str(people.username))
        test = redditor.message(SUBJECT, BODY)
        list_of_redditors[:] = []           #Temporary. Must fix this
    print("***** Messages sent *****")
    return

#Replies to a comment that contains the string of the variable OP_DELIVER
def post_reply(reddit):
    try:
        for people in list_of_redditors:
            comment = praw.models.Comment(reddit, people.comment_id)
            bot_comment = comment.reply(reply_message)
            print(bot_comment) #comment ID
            print("***** Replied to comment *****")
            return
    except:
        print "Will try to post the reply again in 10 minutes..."
        time.sleep(600)
        post_reply(reddit)

#Checks if a file already contains a certain ID. Returns TRUE if it already contains the ID.
def check_file(submission, current_file):   #Pass the file even though it's global to determine with file to check
    current_file.seek(0, 0) #Go to the beggining of the file
    if os.stat(current_file.name).st_size != 0:  #Checks if the file is empty or not
        s = mmap.mmap(current_file.fileno(), 0, access=mmap.ACCESS_READ)

        if s.find(submission) == -1:
            #current_file.write(submission + '\n')
            #print "ID was written to current file"
            return False
        else:
            #print "Already written to the current file."
            return True
    else:
        #current_file.write(submission + '\n')
        return False

#Writes to the file. Fix with error checking. #Pass the file even though it's global to determine with file to write to
def write_to_file(current_file, data):
    current_file.write(data + '\n')


#================================= MAIN ========================================

def main():
    #reddit_threads_file.close()
    #reddit_threads_file.closed #file is opened or closed

    while True:
        reddit = praw.Reddit('bot1')
        subreddit = reddit.subreddit('testingground4bots').hot(limit=5)

        search_for_comment(subreddit)

        if list_of_redditors:
            post_reply(reddit)
            send_message(reddit)
        else:
            print("Nothing found")

if __name__ == '__main__':
    main()
