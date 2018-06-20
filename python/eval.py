import os
import xml.etree.ElementTree
import pytrec_eval
import pandas
import requests
import json

with open('config.json', 'r') as f:
    config = json.load(f)

URL = config['ELASTIC'] + config['ABSTRACTS'] + '/_search'
HEADERS = {'Content-type': 'application/json'}
    
def get_topics(topics_file):
    input_topics = xml.etree.ElementTree.parse(topics_file).getroot().findall('topic')
    topics_dict = {}
    for t in input_topics:
        topic = int(float(t.get('number')))
        topics_dict[topic] = {  'topic': topic,
                                'disease': t.find('disease').text,
                                'gene': t.find('gene').text,
                                'demographic': t.find('demographic').text}
        
    topics_df = pandas.DataFrame.from_dict(topics_dict, orient='index')
    topics_df  = topics_df [['topic', 'disease', 'gene', 'demographic']]
    return(topics_dict, topics_df)

def get_qrels(qrel_file):
    assert os.path.exists(qrel_file)
    with open(qrel_file, 'r') as f_qrel:
        qrels = pytrec_eval.parse_qrel(f_qrel)
    return(qrels)


def run(run_id, topics_dict):
    
    run_dict_pytrec_eval = {}
    run_output_file = []
    
    print('RUN:', run_id)
    
    for topic_tuple in sorted(topics_dict.items()):
        topic_num = topic_tuple[0]
        topic = topic_tuple[1]
        print('TOPIC:', topic['topic'], topic['disease'], topic['gene'], topic['demographic'])

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

        rank = 1
        for hit in response.json()["hits"]["hits"]:
            #print(topic_num, "Q0", hit["_id"], rank, hit["_score"], run)

            #Build dict for pytrec_eval
            if str(topic_num) not in run_dict_pytrec_eval.keys():
                run_dict_pytrec_eval[str(topic_num)] = {}
            run_dict_pytrec_eval[str(topic_num)][hit["_id"]] = hit["_score"]

            #Build list to export to file
            row_tuple = str(topic_num), "Q0", hit["_id"], str(rank), str(hit["_score"]), run_id
            run_output_file.append(row_tuple)
            rank = rank + 1
            
    return(run_dict_pytrec_eval, run_output_file)