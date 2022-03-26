import pandas as pd

cpe_dict_xml_url = "https://nvd.nist.gov/feeds/xml/cpe/dictionary/official-cpe-dictionary_v2.3.xml.zip"

df = pd.read_xml(cpe_dict_xml_url, xpath=".//doc:cpe-item", namespaces={'doc': 'http://cpe.mitre.org/dictionary/2.0'})
df.to_csv('text.csv')
