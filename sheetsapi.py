from __future__ import print_function
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools


# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = '1hfDCSJq5OySTZ8WM5bMV8hHA4s93yJCIqGMKsjmABys'
EVERYTHING_RANGE_NAME = 'C: 10th Term Voting Record!A1:CV'

# indexing is row, col


def get_service():
    """Return a Service object, from which you can make requests"""
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('sheets', 'v4', http=creds.authorize(Http()))
    return service


def process(data: list):
    # return a username list (D3:like D140), (without u/)
    # and a dict with bill names (I2:BA2) as keys, pointing to a list of who
    # voted (I3: ~BA140), where that voted list corresponds to the username one
    #
    # Todo: determine these constants programmicly
    #
    toreturn = {'usernames': [], 'bills': {}}
    username_col = 2
    bill_row = 1
    bill_col_start = 8
    end_row = 139
    end_col = 24  # ish
    for row in data[bill_row+1: end_row]:
        toreturn['usernames'].append(row[username_col])

    for bill_name in data[bill_row][bill_col_start:end_col]:
        toreturn['bills'][bill_name] = []

    for r in range(bill_row+1, end_row):
        for c in range(bill_col_start, end_col):
            bill_name = data[bill_row][c]
            toreturn['bills'][bill_name].append(data[r][c])

    return toreturn


def push_raw(raw_data: list):
    get_service().spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range='Members!A2:I',  # TODO: change me!
        body=raw_data,
        valueInputOption='USER_ENTERED'
    ).execute()
    pass


def push(data):
    # some call to push_raw after data transformations probably
    pass


def get_raw():
    """Get the raw data for the entire sheet"""

    # Call the Sheets API
    result = get_service().spreadsheets().values().get(
      spreadsheetId=SPREADSHEET_ID, range=EVERYTHING_RANGE_NAME
    ).execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
    else:
        print('Yay we had data')
    return values


if __name__ == '__main__':
    result = process(get_raw())
    for key in result:
        print(result[key])
