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
                "cpe": { "type": "text" },
                "title": { "type": "text" },
            }
        }
	}
    print("creating 'cpes' index")
    es.indices.create(index = 'cpes', body = request_body)


def update_index(df):
    if not es.indices.exists('cpes'):
        print("Creating index 'cpes'")
        create_index()
    
    helpers.bulk(es, gendata(df))

def main(args):

    if args.CREATE_INDEX:
        create_index()

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

    es.indices.refresh('cpes')
    # res = es.cat.count('cpes', params={"format": "json"})
    # print(res)

    print(f"Finding the corresponding CPE for {name}...")

    result = es.search(body={"query": {"match": {"title":name}}}, index = 'cpes', size=args.MAX_RESULTS)
    print(result['hits']['hits'])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--create-index', dest="CREATE_INDEX", help="create index 'cpes'", default=False)
    parser.add_argument('--update', action="store_true", dest="UPDATE", help="update index with the latest CPE dictionary data", default=False)
    parser.add_argument('-n', '--name', dest="NAME", help="the application name", default=None)
    parser.add_argument('--csvfile', action="store_true", dest="CSV_FILE", help="save the csv file containing the cpe dictionary data", default=False)
    parser.add_argument('--max-results', type=int, dest="MAX_RESULTS", help="maximum number of results for the given title", default=1)
    args = parser.parse_args()

    main(args)
