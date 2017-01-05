#!/usr/bin/env python
import praw

#The lowercase string that it searches for (will be op_deliver!)
OP_DELIVER = "eat less"

def main():
    reddit = praw.Reddit('bot1') #Refers to [bot1] in praw.ini file
    subreddit = reddit.subreddit('AskReddit').hot(limit=3) #Get the top 3 hot AskReddit threads

    author = search_for_comment(subreddit)
    print author


#Searches for a match and returns the commentors username
def search_for_comment(subreddit):
    # "Submission" contains each AskReddit thread
    for submission in subreddit:
        submission.comments.replace_more(limit=0) #Get rid of "more" comments

        #Finds comments that match with "op_deliver!" or whatever is in the OP_DELIVER variable
        for comment in submission.comments.list():
            if comment.body.lower() == OP_DELIVER:
                return comment.author

if __name__ == '__main__':
    main()
