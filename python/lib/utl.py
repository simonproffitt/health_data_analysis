#
# Utility functions, todo split these into more meaningful
# libraries when we have more of them
#

import requests
import json
import urllib
import zipfile
import os
import pandas

def prettyPrint(rawjson):
    print(json.dumps(rawjson, indent=2))

def prettyDfSize(df):
    print('Rows: {}, Columns: {}'.format(len(df), len(df.columns)))

def get(url):
    print(url)
    result = {
        'successful' : False,
        'raw' : None,
        'json' : None
    }
    r = requests.get(url)
    result['raw'] = r
    if(r.status_code != 200):
        print('Error returned for {}: {}'.format(r.url, r.status_code))
        print(r.text)
    else:
        result['successful'] = True
        result['json'] = json.loads(r.text)
    return result

# given the location of a file
def get_csv_data_from_url(url):
    os.makedirs('./_cache', exist_ok=True)
    filename =  url.split('/')[-1]
    filepath = './_cache/' + url.split('/')[-1]
    folderpath = '._cache/' + filename.split('.')[0]
    if (~os.path.isfile(filepath)):
        urllib.request.urlretrieve(url, filepath)
        zf = zipfile.ZipFile(filepath)
        zf.extractall(path=folderpath)
        zf.close()
    csvs = [folderpath + '/' + csv for csv in os.listdir(folderpath) if csv.endswith('csv')]
    return pandas.concat([read_terrible_csv_file_format(csv) for csv in csvs])

def uniq(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def read_terrible_csv_file_format(csvfile):
    f = open(csvfile,'r')
    #
    [f.readline().split(',') for x in range(8)]
    header = f.readline().rstrip('\n').lstrip('"').split('","')
    lines = [x.rstrip('\n').lstrip('"').split('","') for x in f][:-1]
    split_columns = [uniq(column.split('~')) for column in header]
    N = max([len(a) for a in split_columns])
    split_columns = [tuple(a + [''] * (N - len(a))) for a in split_columns]
    return pandas.DataFrame(dict(zip(split_columns,list(zip(*lines)))))


#https://medium.com/@amirziai/flattening-json-objects-in-python-f5343c794b10#.5ml75lajr
def flatten_json(y):
    out = {}

    def flatten(x, name=''):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + '_')
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + str(i) + '_')
                i += 1
        else:
            out[name[:-1]] = x

    flatten(y)
    return out
