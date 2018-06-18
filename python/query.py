import json
import requests
import xml.etree.ElementTree
import operator
import pprint

URL = 'http://trectrectrec.ddns.net:9200/trec/_search'
HEADERS = {'Content-type': 'application/json'}
input_topics = xml.etree.ElementTree.parse('topics2017.xml').getroot().findall('topic')

topics = {}
trec_eval = {}

for t in input_topics:

    # Read from file
    topic = int(float(t.get('number')))
    topics[topic] = {'topic': topic,
                    'disease': t.find('disease').text,
                    'gene': t.find('gene').text.replace('Amplification',''),
                    'demographic': t.find('demographic').text}

for topic_tuple in sorted(topics.items()):
    topic_num = topic_tuple[0]
    topic = topic_tuple[1]
    #print(topic['topic'], topic['disease'], topic['gene'], topic['demographic'])

    # For query...
    # Fill template with query
    with open('query.json', 'r') as myfile:
      query = myfile.read()  #print(data)
      query = query.replace('{{disease}}', topic['disease'])
      query = query.replace('{{gene}}', topic['gene'])
      query = query.replace('{{demographic}}', topic['demographic'])
      #print(query)

    response = requests.post(URL, data=query, headers=HEADERS)
    #print(response.json())

    run = "my_run"
    rank = 1
    for hit in response.json()["hits"]["hits"]:
        print(topic_num, "Q0", hit["_id"], rank, hit["_score"], run)
        rank = rank + 1

    # Send query
    #trec_eval
quit()


URL = 'http://trectrectrec.ddns.net:9200/trec/_search'
with open('query.json', 'r') as myfile:
  data = myfile.read()  #print(data)

# replace placeholders

data_json = json.dumps(data)

headers = {'Content-type': 'application/json'}
response = requests.post(URL, data=data, headers=headers)

#print(response.json())

run = "my_run"
topic = 1
rank = 1

for hit in response.json()["hits"]["hits"]:
    print(topic, "Q0", hit["_id"], rank, hit["_score"], run)
    rank = rank + 1
