# cpe-detection-system

ssh -i ~/.ssh/id_rsa -L 10000:vpc-cpe-softwares-xut4os46csf5fnb2ycxijwbfk4.eu-west-2.es.amazonaws.com:443 ubuntu@35.177.25.10

https://vpc-cpe-softwares-xut4os46csf5fnb2ycxijwbfk4.eu-west-2.es.amazonaws.com/_plugin/kibana/

To delete index:
curl -k -X DELETE 'https://localhost:10000/cpes'

curl -k -XGET --header 'Content-Type: application/json' https://localhost:10000/cpes/_search -d '{
    "query" : {
        "multi_match" : {
            "query" : "Intel Atom C2508 Firmware",
            "fields": ["title^10", "cpe^3"]
        } 
    },
    "size" : 2
}'