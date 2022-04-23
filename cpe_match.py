import pandas as pd
from elasticsearch import Elasticsearch, helpers
import configparser
import argparse

CPE_DICT_URL = "https://nvd.nist.gov/feeds/xml/cpe/dictionary/official-cpe-dictionary_v2.3.xml.zip"

config = configparser.ConfigParser()
config.read('credentials')

es = Elasticsearch(
    cloud_id=config['ELASTIC']['cloud_id'],
    basic_auth=(config['ELASTIC']['user'], config['ELASTIC']['password'])
)

def update_index():
    df = pd.read_xml(CPE_DICT_URL, xpath=".//doc:cpe-item", namespaces={'doc': 'http://cpe.mitre.org/dictionary/2.0'})
    df.to_csv('cpes.csv')

    # for i in range(len(df)):
    #     es.index(
    #     index='cpe-match',
    #     document={
    #     'cpe': df['name'].values[i],
    #     'title': df['title'].values[i]
    #     })

    # es.indices.refresh(index='cpe-match')
    actions = []
    counter = 0

    for i in range(100):#range(len(df)):
        source = {
        'cpe': df['name'].values[i],
        'title': df['title'].values[i]
        }
        action = {
        '_op_type': 'index',
        '_index': 'cpes',
        '_id': counter,
        'doc': source
        }
        actions.append(action)
        counter += counter
        if len(actions) >= 10:
            helpers.bulk(es, actions)
            del actions[0:len(actions)]

    if len(actions) > 0:
        helpers.bulk(es, actions)

def main(args):
    if args.UPDATE:
        update_index()
        exit(0)

    no_results = args.MAX_RESULTS
    if no_results < 0:
        print("Max results have to be greather than 0")
        exit(1)

    # Application name
    name = args.NAME
    if name is None:
        print("The application name have to be specified")
        exit(1)

    print(f"Finding the corresponding CPE for {name}...")

    result = es.search(
        index='cpes',
        query={
        'match_all': {}
        }
    )

    print(result['hits']['hits'])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--update', action="store_true", dest="UPDATE", help="update index with the latest CPE dictionary data", default=False)
    parser.add_argument('-n', '--name', dest="NAME", help="the application name", default=None)
    parser.add_argument('--csvfile', action="store_true", dest="CSV_FILE", help="get the csv file containing the cpe dictionary data", default=False)
    parser.add_argument('--max-results', type=int, dest="MAX_RESULTS", help="maximum number of results for the given title", default=1)
    args = parser.parse_args()

    main(args)
