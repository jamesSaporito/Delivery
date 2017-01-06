#!/usr/bin/env python

import praw

OP_DELIVER = "op_deliver!"
SUBJECT = "Delivery Bot"
BODY = "I will let you know if OP Delivers."
list_of_redditors = list() #Should be a list of classes "RedditorsSubscribed"

#================================= CLASSES =====================================

class RedditorsSubscribed():
    def __init__(self, username, submission_id):
        self.username = username
        self.submission_id = submission_id
        #self.comment_replied_to = comment_replied_to

#================================= FUNCTIONS ===================================

#Finds comments that match with the OP_DELIVER variable and appends the class RedditorsSubscribed instance to "list_of_redditors"
def search_for_comment(subreddit):
    for submission in subreddit:
        submission.comments.replace_more(limit=10)

        for comment in submission.comments.list():
            if comment.body.lower() == OP_DELIVER:
                list_of_redditors.append(RedditorsSubscribed(comment.author, submission.id))

#Sends message to a user.
def send_message(reddit):
    redditor = praw.models.Redditor(reddit, list_of_redditors[0].username)
    redditor.message(SUBJECT, BODY)
    print("***** Messages sent *****")

def post_reply(): #START HERE AND HAVE THE BOT POST A REPLY
    return

#================================= MAIN ========================================

def main():
    while True:
        reddit = praw.Reddit('bot1')
        subreddit = reddit.subreddit('AskReddit').hot(limit=8)
        search_for_comment(subreddit)

        if list_of_redditors:
            send_message(reddit)
        else:
            print("Nothing found")

if __name__ == '__main__':
    main()
