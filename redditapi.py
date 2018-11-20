
"""
Base class for general reddit side operations.
"""

import praw
import datetime as dt
import json

VERSION = "0.3.0"


def warning_info(problem, details):
    # todo: should I output this to a file or something?
    print("\n\nWarning!")
    print(problem)
    print("details: {}".format(details))
    pass


def is_voting(submission_name):
    if len(submission_name) < 7:
        return False
    if not(submission_name.startswith('B') or submission_name.startswith('M')):
        return False
    try:
        int(submission_name[1:2])
    except ValueError:
        return False
    else:
        return True


class RedditFetch:
    def __init__(self, users: list, sheet_data: dict):
        with open("reddittoken.json", "r") as f:
            creds = json.load(f)
        my_id = creds["id"]
        secret = creds["secret"]
        my_username = creds['username']
        # ua = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:63.0)" \
        #     " Gecko/20100101 Firefox/63.0"
        ua = 'linux:{}:{} (by /u/{})'.format(my_id, VERSION, my_username)
        self.reddit = praw.Reddit(
          client_id=my_id,
          client_secret=secret,
          user_agent=ua
        )
        self.users = users
        print(users)
        self.posts = []
        self.sheet_data = sheet_data
        self.unrecognized_users = []

    def populatePosts(self):
        subreddit = self.reddit.subreddit('MHOCMP')
        now = dt.datetime.now()
        tendays = dt.timedelta(days=10)

        for submission in subreddit.new(limit=6):
            if is_voting(submission.title):
                print(submission.title)
                self.posts.append(submission)

                created = dt.datetime.fromtimestamp(int(submission.created))
                # print(now - created)
                if now - created > tendays:
                    print("too old!")
                    break

    def index(self, username):
        # returns the index of a username in the username list
        try:
            i = self.users.index(username)
        except ValueError:
            if username != 'AutoModerator':
                warning_info("Commenter not found on user list", username)
                if username not in self.unrecognized_users:
                    self.unrecognized_users.append(username)
            return None
        else:
            return i

    def collectData(self):
        self.populatePosts()
        print(self.posts)

        for submission in self.posts:
            # Don't truncate the comments
            submission.comments.replace_more(limit=60)
            comments = submission.comments.list()
            print("{} has {} comments".format(submission.title, len(comments)))

            # Get the bill identifier (like B708).
            bill_id_end = submission.title.find(' ')
            bill_id = submission.title[:bill_id_end]
            print('"'+bill_id+'"')
            # Make sure the bill indentifier is in our list
            new_bill = False
            if bill_id not in self.sheet_data.keys():
                self.sheet_data[bill_id] = [None] * len(self.users)
                new_bill = True

            commenter_names = []
            for comment in comments:
                if "aye" in comment.body.lower() \
                        or "nay" in comment.body.lower() \
                        or "abstain" in comment.body.lower():
                    commenter_names.append(comment.author.name)
                    author_index = self.index(comment.author.name)
                    if author_index is None:
                        pass  # already sent a # warning
                    elif "aye" in comment.body.lower():
                        self.sheet_data[bill_id][author_index] = 'AYE'
                    elif "nay" in comment.body.lower():
                        self.sheet_data[bill_id][author_index] = 'NAY'
                    elif "abstain" in comment.body.lower():
                        self.sheet_data[bill_id][author_index] = 'ABS'

            for user in self.users:
                if user not in commenter_names:
                    user_index = self.index(user)
                    # Here we assume that anyone with a crossed out name has
                    #  N/A across their entire row
                    if self.sheet_data[bill_id][user_index] != 'N/A':
                        self.sheet_data[bill_id][user_index] = 'DNV'
            if new_bill:
                print(self.sheet_data[bill_id])

    def run(self):
        self.populatePosts()
        self.collectData()
        print('--------\nThese users were not recognized from the sheet:\n')
        for user in self.unrecognized_users:
            print(user)
        return self.sheet_data
