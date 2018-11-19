
"""
Base class for general reddit side operations

-dms people on "Active lists" telling them to comment, if they don't it repeats the dm every day for the whole of that reading (3 days iirc)
-dms people on "active lists" reminding them to write their bills(or how many they have left)
-dms people asking them to ask their mqs, 2 for everyone and 6 for spokespersons
-dms MPs telling them there is a vote, but firstly asks seimer to Whip, aye, no, abstain or free vote

 mqs require 2 questions,
 bills and motions require 1

"""

import praw
from discord.ext import commands
import rethinkdb as r
import datetime as dt
import json


class RedditBase():
    def __init__(self, bot):
        self.bot = bot
        self.conntask = self.bot.loop.create_task(self.connectToRethinkdb())
        self.bgtimer = None
        creds = json.load("reddittoken.json")
        my_id = creds["id"]
        secret = creds["secret"]
        ua = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML,"\
             " like Gecko) Chrome/65.0.3325.183 Safari/537.36 Viv/1.96.1147.55"
        self.reddit = praw.Reddit(
          client_id=my_id,
          client_secret=secret,
          user_agent=ua
        )
        self.parsedDict = None
        self.posts = None
        self.users = {}

    def __unload(self):
        self.bot.loop.create_task(self.conn.close())
        print('reddit.py unload routine called')
        if self.bgtimer is not None:
            self.bgtimer.cancel()

    async def makeUsersDict(self):
        """
        Make our users dict.
        :param:
        :return:  dict of class Redditor, with keys being the redditor username
        """
        users = {}
        cursor = await r.db('mhoc').table("discord").run(self.conn)
        while await cursor.fetch_next():
            c = await cursor.next()
            print(c)
            try:
                reddit = c['reddit']
            except KeyError:
                pass
            else:
                if c['discord'] is not None:
                    users[reddit] = Redditor(reddit, str(c['discord']))
        self.users = users
        return users

    async def populatePosts(self):
        reddit = self.reddit
        subreddit = reddit.subreddit('MHOC')

        now = dt.datetime.now()
        threedays = dt.timedelta(days=3)

        self.posts = {"MQs": [], "BILL": [], "MOTION": []}

        for submission in subreddit.new(limit=60):
            print(submission.link_flair_text)
            if submission.link_flair_text in self.posts.keys():
                print(submission.title)
                self.posts[submission.link_flair_text].append(submission)

                created = dt.datetime.fromtimestamp(int(submission.created))
                print(now - created)
                if now - created > threedays:
                    print("too old!")
                    break

    @commands.cooldown(rate=3, per=7)
    @commands.command()
    async def update(self, ctx):
        """
        Update what the bot thinks about who's been active about what and stuff
        Basically do everything but output.
        :param ctx:
        :return:
        """
        await self.collectData()
        await ctx.send("Data collection successful.")

    async def collectData(self):
        await self.makeUsersDict()
        await self.populatePosts()
        print(self.posts)

        for key in ['BILL', 'MOTION']:
            for submission in self.posts[key]:
                submission.comments.replace_more(limit=10)
                comments = submission.comments.list()
                print(len(comments))

                participants = []
                for comment in comments:
                    if len(comment.body) > 15:
                        if comment.author.name in self.users:
                            participants.append(comment.author.name)
                    else:
                        pass
                for username in self.users:
                    user = self.users[username]
                    if key == "BILL":
                        if username in participants:
                            user.commentedBills.append(submission)
                        else:
                            user.uncommentedBills.append(submission)
                    elif key == "MOTION":
                        if username in participants:
                            user.commentedMotions.append(submission)
                        else:
                            user.uncommentedMotions.append(submission)

            # Now do MQs
            for submission in self.posts["MQs"]:
                submission.comments.replace_more(limit=10)
                comments = submission.comments.list()
                print(len(comments))

                onetime_participants = []
                twotime_participants = []
                for comment in comments:
                    if len(comment.body) > 15:
                        authorname = comment.author.name
                        if authorname in self.users:  # something is wrong here
                            if authorname in onetime_participants:
                                onetime_participants.remove(authorname)
                                twotime_participants.append(authorname)
                            elif authorname not in twotime_participants:  # if the comment thrice, don't screw up
                                onetime_participants.append(authorname)
                    else:
                        pass
                        # print(comment.body)
                for username in self.users:
                    user = self.users[username]
                    if username in twotime_participants:
                        user.commentedMQs.append(submission)
                    elif username in onetime_participants:
                        user.partiallyCommentedMQs.append(submission)
                    else:
                        user.uncommentedMQs.append(submission)
        print(self.users)

    @commands.cooldown(rate=3, per=7)
    @commands.command()
    async def debugOutputUsers(self, ctx):
        """
        Prints the current content of the Users dict onto discord
        :param ctx:
        :return:
        """
        n = 1
        message = "self.users:\n\n"
        for username in self.users:
            user = self.users[username]
            if n % 3 == 0:
                await ctx.send(message)
                message = "_ _\n\n" + str(user)
            else:
                message += "\n" + str(user)
            n += 1
        if n % 3 is not 0:
            await ctx.send(message)
        await ctx.send("Done.")


def setup(bot):
    bot.add_cog(RedditBase(bot))


class Redditor():
    def __init__(self, redditname, discordid):
        self.commentedBills = []
        self.uncommentedBills = []
        self.commentedMotions = []
        self.uncommentedMotions = []
        self.commentedMQs = []
        self.partiallyCommentedMQs = []
        self.uncommentedMQs = []

        self.redditname = redditname
        self.discordid = discordid
        self.discordmention = "<@{}>".format(discordid)

    def __str__(self):
        string = "{} aka {}".format(self.redditname, self.discordmention)
        string += "\n Uncommented bills: {}".format(self.uncommentedBills)
        string += "\n Uncommented motions: {}".format(self.uncommentedMotions)
        string += "\n Uncommented MQs: {}".format(self.uncommentedMQs)
        string += "\n Only one comment on MQs: {}".format(
            self.partiallyCommentedMQs)
        string += "\n\n"
        return string

    def __repr__(self):
        return str(self)

    def getTotalCommentedPosts(self):
        return len(self.commentedBills) + len(self.commentedMotions) + len(self.commentedMQs)

    def getTotalUncommentedPosts(self):
        return len(self.uncommentedBills) + len(self.uncommentedMotions) + len(self.uncommentedMQs) + \
               len(self.partiallyCommentedMQs)
