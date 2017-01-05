import praw

OP_DELIVER = "op_deliver!"

reddit = praw.Reddit('bot1')
subreddit = reddit.subreddit('AskReddit').hot(limit=3) #Get the top 3 hot AskReddit threads

#Submission contains each AskReddit thread
for submission in subreddit:
    submission.comments.replace_more(limit=0) #Get rid of "more" comments

    #Finds comments that match with "op_deliver!" or whatever is in the OP_DELIVER variable
    for comment in submission.comments.list():
        if comment.body.lower() == OP_DELIVER:
            print "MATCH"
        else:
            print "NO MATCH"
