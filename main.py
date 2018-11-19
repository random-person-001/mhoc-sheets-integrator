import sheetsapi
import redditapi


# get sheet data and stuff
# make call to sheets api module
data = sheetsapi.fetch()
users = data['users']
bills = data['bills']

# get current voting data from reddit
# make call to reddit api module

# create data structure similar to that of sheet
# do some processing, populate it

# push new data structure to the sheet
# make call to sheets api module

# yay
# party; we're done
