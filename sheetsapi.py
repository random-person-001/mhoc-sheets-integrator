from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools


# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/spreadsheets'

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = '1hfDCSJq5OySTZ8WM5bMV8hHA4s93yJCIqGMKsjmABys'
EVERYTHING_RANGE_NAME = 'C: 10th Term Voting Record!A1:CV'
BILL_RANGE_NAME = 'C: 10th Term Voting Record!I2:CV'  # Includes bill names

# indexing is row, col


def transpose(old):
    """Assumes rectangular array"""
    return list(map(list, zip(*old)))


class SheetsInterfacer:
    def __init__(self):
        self.username_col = 2
        self.bill_row = 1
        self.bill_col_start = 8
        self.end_row = 139
        self.end_col = 52  # ish

        self.user_list = []
        self.bill_list = []  # just their names, and ordered

    def get_service(self):
        """Return a Service object, from which you can make requests"""
        # The file token.json stores the user's access and refresh tokens, and
        # is created automatically when the authorization flow completes for
        # the first time.
        store = file.Storage('token.json')
        creds = store.get()
        if not creds or creds.invalid:
            flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
            creds = tools.run_flow(flow, store)
        service = build('sheets', 'v4', http=creds.authorize(Http()))
        return service

    def process(self, data: list):
        # return a username list (D3:like D140), (without u/)
        # and a dict with bill names (I2:BA2) as keys, pointing to a list of
        # who voted (I3: ~BA140), where that voted list corresponds to the
        # username one
        #
        # Todo: determine these constants programmicly
        #
        toreturn = {'usernames': [], 'bills': {}}
        for row in data[self.bill_row+1: self.end_row]:
            toreturn['usernames'].append(row[self.username_col])
            self.user_list.append(row[self.username_col])

        for bill_name in data[self.bill_row][self.bill_col_start:self.end_col]:
            toreturn['bills'][bill_name] = []
            self.bill_list.append(bill_name)

        for r in range(self.bill_row+1, self.end_row):
            for c in range(self.bill_col_start, self.end_col):
                bill_name = data[self.bill_row][c]
                toreturn['bills'][bill_name].append(data[r][c])

        return toreturn

    def push_raw(self, raw_data: list):
        self.get_service().spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=BILL_RANGE_NAME,
            body={'values': raw_data},
            valueInputOption='USER_ENTERED'
        ).execute()

    def push(self, data):
        raw = []

        # update the stuff that we already had
        for billname in self.bill_list:
            row = data.pop(billname)
            row.insert(0, billname)
            raw.append(row)
        # add the new stuff
        print("\nnow adding new bills\n")
        for billname in data:
            if billname is not None and data[billname] is not None:
                row = data[billname]
                row.insert(0, billname)
                print(row)
                raw.append(row)

        self.push_raw(transpose(raw))

    def get_raw(self):
        """Get the raw data for the entire sheet"""
        # Call the Sheets API
        result = self.get_service().spreadsheets().values().get(
          spreadsheetId=SPREADSHEET_ID, range=EVERYTHING_RANGE_NAME,
          majorDimension='ROWS'
        ).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
        else:
            print('Yay we had data')
        return values

    def fetch(self):
        # Do all the things on the front side
        return self.process(self.get_raw())


if __name__ == '__main__':
    result = SheetsInterfacer().fetch()
    for key in result:
        print(result[key])
