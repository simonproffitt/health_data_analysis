#


# Librify work Carole did to understand the ONS api
#

import json
import pandas
import utl as utl
import requests
from pandas.io.json import json_normalize


# ONS api url
base_url = 'http://data.ons.gov.uk/ons/api/data'

## Get the available contexts
def get_contexts(api_key):
    url = '{}/contexts.json?apikey={}'.format(base_url, api_key)
    response = utl.get(url)
    if response['successful'] == False:
        print('Error')
        return pandas.read_json(['{}'])
    else:
        return json_normalize(response['json']['ons']['contextList']['statisticalContext'])

## get the available concepts for a given context
def get_concepts(context,api_key):
    url = '{}/concepts.json?apikey={}&context={}'.format(base_url, api_key,context)
    response = utl.get(url)
    if response['successful'] == 'False':
        print('Error')
    else:
        concepts = [concept for concept in response['json']['ons']['conceptList']['concept']]
        temp = {'name':[], 'id':[], 'usage_number':[]}
        for concept in concepts:
            temp['id'].append(concept['id'])
            temp['usage_number'].append(concept['collectionCount'])
            temp['name'].append([name for name in concept['names']['name'] if name['@xml.lang'] == 'en'][0]['$'])
        conceptsdf = pandas.DataFrame(temp)
        conceptsdf['id'] = conceptsdf['id'].astype(int)
        return conceptsdf

## get classifications for a given context
def get_classifications(context,api_key):
    url = '{}/classifications.json?apikey={}&context={}'.format(base_url, api_key, context)
    r = utl.get(url)
    if r['successful'] == False:
        print('Error')
    else:
        classifications = [classification for classification in r['json']['ons']['classificationList']['classification']]
        temp = {'name':[], 'id':[], 'url':[]}
        temp['id'] = [classification['id'] for classification in classifications]
        temp['name'] = [[name['$'] for name in classification['names']['name'] if name['@xml.lang'] == 'en'][0] for classification in classifications]
        temp['url'] = [[url['href'] for url in classification['urls']['url'] if url['@representation'] == 'json'][0] for classification in classifications]
        classificationsdf = pandas.DataFrame(temp)
        return (classificationsdf)


##for a given context, classification get details
def get_classification_details(context,classification,api_key):
    classifications = get_classifications(context,api_key)
    classifications_filtered = classifications[classifications.name == classification]
    for index, classification in classifications_filtered.iterrows():
        urlarg = classification['url']
        url = '{}/{}'.format(base_url, urlarg)
        print(url)
        r = requests.get(url)
        if(r.status_code != 200):
            print('Error returned for {}: {}'.format(r.url, r.status_code))
            print(r.text)
        else:
            try:
                raw = json.loads(r.text)
                codes = [code for code in raw['Structure']['CodeLists']['CodeList']['Code']]
                temp = {'description':[], 'value':[]}
                temp['value'] = [code['@value'] for code in codes]
                temp['description'] = [[desc['$'] for desc in code['Description'] if desc['@xml.lang'] == 'en'][0] for code in codes]
                codesdf = pandas.DataFrame(temp)
                return codesdf.sort_values(['description'])
            except TypeError:
                # saw that happening where Description is not an array for some reasons...
                print("TypeError:", sys.exc_info()[0])

# for a given context and classification get the collections available
def get_collections_for_classification(context,classification,api_key):
    url = '{}/collections.json?apikey={}&context={}&find={}'.format(base_url, api_key, context, classification)
    response = utl.get(url)
    if response['successful'] == False:
        print('Error')
    else:
        print('Dataset for ', classification)
        content = response['json']
        temp = {'name' : [], 'description' : [], 'id' : [], 'url' : [], 'geohierarchy' : []}
        for collection in content['ons']['collectionList']['collection']:
            temp['name'].append([n for n in collection['names']['name'] if n['@xml.lang'] == 'en'][0]['$'])
            temp['description'].append(collection['description'])
            temp['id'].append(collection['id'])
            temp['url'].append([u for u in collection['urls']['url'] if u['@representation'] == 'json'][0]['href'])
            temp['geohierarchy'].append(collection['geographicalHierarchies'])
            df = pandas.DataFrame(temp)
        return df.sort_values(['description'])

# for a given context, classification and collection get the urls for the data sets
# ons.get_dataset_details_for_classification_collection('Census','Religion','Religion by sex by age',<<api_key>>)
def get_dataset_details_for_classification_collection(context,classification,collection_name,api_key):
    collections = get_collections_for_classification(context,classification,api_key)
    collections = collections[collections.name == collection_name]
    urls = pandas.concat([json_normalize(utl.get(base_url + '/' + a)['json']) for a in collections['url']])
    #http://stackoverflow.com/questions/952914/making-a-flat-list-out-of-list-of-lists-in-python
    urls = [url['href'] for urllist in urls['ons.collectionDetail.urls.url'].values for url in urllist if url['@representation']=='json']
    details = pandas.concat([json_normalize(utl.get(base_url + '/' + url)['json']) for url in urls])
    # get the english csvs
    details['file_url'] = [a['href']['$'] for a in details['ons.datasetDetail.documents.document'] for a in a if (a['@type']=='CSV') & (a['href']['@xml.lang']=='en')]
    details['geography'] = [b['$'] for b in details['ons.datasetDetail.geographicalHierarchies.geographicalHierarchy.names.name'] for b in b if b['@xml.lang'] =='en']
    details['collection_name'] = collection_name
    return details[['collection_name','geography','file_url']]

def get_dataset_for_classification_collection_geography(context,classification,collection_name,geography,api_key):
    datasets = get_dataset_details_for_classification_collection(context,classification,collection_name,api_key)
    datasets = datasets[datasets.geography == 'geography']
    [get_all_data(a['set_url']) for a in datasets]
