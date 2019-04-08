# mhoc-sheets-integrator
Track votes for the reddit Model House of Commons sim in a spreadsheet.

## Setup
Using this will require a reddit api token and some sheets authenitcation stuff.  To interface with these, the `praw` and various google packages are needed.  See [here](https://developers.google.com/sheets/api/quickstart/python) for a rough guide to getting started.  After setting up, the sheets integration should make a `token.json` and `credentials.json`.  For praw credentials, make a file called `reddittoken.json` with the following format:
```json
{
  "secret": "[long string]",
  "id": "[shorter string]",
  "username": "[your reddit username]"
}
```

You'll probably also want to edit the `SPREADSHEET_ID` variable in sheetsapi.py.  Then you should probably be good.  
