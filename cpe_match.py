import pandas as pd
import argparse
from elasticsearch import Elasticsearch, helpers
import requests

from const import (
    ES_HOST,
    ES_PORT
)

from test_mappings import ApplicationCpeMapping

application_cpe_mapping = ApplicationCpeMapping().WELL_KNOWN_APPLICATION_CPE


CPE_DICT_URL = "https://nvd.nist.gov/feeds/xml/cpe/dictionary/official-cpe-dictionary_v2.3.xml.zip"

es = Elasticsearch(
    host=ES_HOST,
    port=ES_PORT,
    scheme="https",
    verify_certs=False,
    ssl_show_warn=False,
)

def load_cpe_data(save_csv_file):
    df = pd.read_xml(CPE_DICT_URL, xpath=".//doc:cpe-item", namespaces={'doc': 'http://cpe.mitre.org/dictionary/2.0'})



    # if save_csv_file:
    #     df.to_csv('cpes.csv')
    return df

def df_from_file():
    df = pd.read_csv('cpes.csv')

    return df

def gendata(df):
    for i in range(len(df)):
        yield {
            "_index": "cpes",
            # "_op_type": 'create',
            # '_id': i,
            "cpe": df['name'].values[i], 'title': df['title'].values[i],
            # 'doc': {"cpe": df['name'].values[i], 'title': df['title'].values[i],}
        }

def create_index():
    request_body = {
        "settings" : {
            "number_of_shards": 2,
            "number_of_replicas": 1
        },
        "mappings": {
            "properties": {
                "cpe": { "type": "text"},
                "title": { "type": "text", "analyzer": "whitespace" },
            }
        }
	}
    es.indices.create(index = 'cpes', body = request_body)


def update_index(df):
    if not es.indices.exists('cpes'):
        print("Creating index 'cpes'")
        create_index()
    
    helpers.bulk(es, gendata(df))

def count_entries():
    es.indices.refresh('cpes')
    res = es.cat.count('cpes', params={"format": "json"})
    print(res)

def search_app_cpe(application_name):
    # print(f"Finding the corresponding CPE for {application_name}...")

    headers = {"Content-Type": "application/json; charset=utf-8"}


    body2 = '''{
        "query": {
            "match": {
                "title": {
                    "query":''' + f'"{application_name}",' + '''
                }
            }
        }
    }
    '''

    body3 = '''{
    "query": {
        "bool": {
            "must": [
                {
                    "match": {
                        "title": ''' + f'"{application_name}"' + '''
                    }
                }
            ],
            "should": [
            {
                "match": {
                        "title": ''' + f'"{application_name}"' + '''
                        
                    }
                }
            ]
        }
    }
    }'''


    import json

    response = requests.get(url='https://localhost:10000/cpes/_search/', data=body3, verify=False, headers=headers)
    # print(response.text)

    if response.status_code == 400:
        print(response.request.url)
    elif response.status_code == 200:
        try:
            return response.json()['hits']['hits']
        except:
            return None

def check_accuracy():
    for key, value in application_cpe_mapping.items():
        cpe = search_app_cpe(key)[0]['_source']['cpe']

        cpe_es = ":".join(cpe.split(':')[2:4])
        cpe_dict = ":".join(value.split(':')[3:5])

        if cpe_es != cpe_dict:
            print(f'CPE {cpe_es} does not match with expected {cpe_dict}')

def main(args):

    # es.indices.delete(index='cpes', ignore=[400, 404])
    # exit(0)

    if args.TEST:
        check_accuracy()
        exit(0)

    if args.UPDATE:
        # df = load_cpe_data(args.CSV_FILE)
        # print('CPE data loaded')
        new_df = df_from_file()
        update_index(new_df)
        exit(0)

    no_results = args.MAX_RESULTS
    if no_results < 0:
        print("Max results have to be greather than 0")
        exit(1)

    # Application name
    name = args.NAME
    if name is None:
        print("The application name has to be specified")
        exit(1)

    # count_entries()
    print(search_app_cpe(name))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--update', action="store_true", dest="UPDATE", help="update index with the latest CPE dictionary data", default=False)
    parser.add_argument('-n', '--name', dest="NAME", help="the application name", default=None)
    parser.add_argument('--csvfile', action="store_true", dest="CSV_FILE", help="save the csv file containing the cpe dictionary data", default=False)
    parser.add_argument('--max-results', type=int, dest="MAX_RESULTS", help="maximum number of results for the given title", default=1)
    parser.add_argument('--test', action="store_true", dest="TEST", help="Test accuracy")
    args = parser.parse_args()

    main(args)
