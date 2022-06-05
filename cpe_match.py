import pandas as pd
import argparse
from elasticsearch import Elasticsearch, helpers
from const import (
    ES_HOST,
    ES_PORT
)

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
    if save_csv_file:
        df.to_csv('cpes.csv')

    return df

def rec_to_actions(df):
    import json
    for record in df.to_dict(orient="records"):
        yield ('{ "index" : { "_index" : "cpes", "_type" : "record" }}')
        yield (json.dumps(record, default=int))

def update_index(df):
    
    # for i in range(len(df)):
    #     es.index(
    #     index='cpe-match',
    #     document={
    #     'cpe': df['name'].values[i],
    #     'title': df['title'].values[i]
    #     })

    # es.indices.refresh(index='cpe-match')
    # actions = []
    # counter = 0

    # for i in range(100):#range(len(df)):
    #     source = {
    #     'cpe': df['name'].values[i],
    #     'title': df['title'].values[i]
    #     }
    #     action = {
    #     '_op_type': 'index',
    #     '_index': 'cpes',
    #     '_id': counter,
    #     'doc': source
    #     }
    #     actions.append(action)
    #     counter += counter
    #     if len(actions) >= 10:
    #         helpers.bulk(es, actions)
    #         del actions[0:len(actions)]

    # if len(actions) > 0:
    r = es.bulk(rec_to_actions(df))
    print(not r['errors'])

def main(args):
    if args.UPDATE:
        df = load_cpe_data(args.CSV_FILE)
        print('CPE data loaded')
        update_index(df)
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

    print(f"Finding the corresponding CPE for {name}...")

    result = es.search(
        index='cpes',
        body={}
        #'match_all': {}
        #}
    )

    print(result['hits']['hits'])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--update', action="store_true", dest="UPDATE", help="update index with the latest CPE dictionary data", default=False)
    parser.add_argument('-n', '--name', dest="NAME", help="the application name", default=None)
    parser.add_argument('--csvfile', action="store_true", dest="CSV_FILE", help="save the csv file containing the cpe dictionary data", default=False)
    parser.add_argument('--max-results', type=int, dest="MAX_RESULTS", help="maximum number of results for the given title", default=1)
    args = parser.parse_args()

    main(args)
