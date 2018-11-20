import sheetsapi
import redditapi

#
# To do:
#   make it determine spreadsheet size constants automatically
#   make it determine spreadsheet name automatically
#   make it account for people with N/A
#

# get sheet data and stuff
# make call to sheets api module
sheets = sheetsapi.SheetsInterfacer()
data = sheets.fetch()
users = data['usernames']
bills = data['bills']

# set up reddit stuff
rf = redditapi.RedditFetch(users, bills)

# gets current voting data from reddit, processes it to insert it into the
# data model that we obtained from the sheet
new_data = rf.run()

# push new data structure to the sheet
# make call to sheets api module
sheets.push(new_data)
