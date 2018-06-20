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

def run_to_pytrec_eval(df):
    run_dict_pytrec_eval = {}
    for index, row in df.iterrows():
        if str(row['TOPIC_NO']) not in run_dict_pytrec_eval.keys():
            run_dict_pytrec_eval[str(row['TOPIC_NO'])] = {}
        run_dict_pytrec_eval[str(row['TOPIC_NO'])][row['ID']] = row['SCORE']
    return(run_dict_pytrec_eval)

def topics_to_pytrec_eval(df):
    topics_dict_pytrec_eval = {}
    for index, row in df.iterrows():
        if row['topic'] not in topics_dict_pytrec_eval.keys():
            topics_dict_pytrec_eval[row['topic']] = {}
        topics_dict_pytrec_eval[row['topic']]['topic'] = row['topic']
        topics_dict_pytrec_eval[row['topic']]['disease'] = row['disease']
        topics_dict_pytrec_eval[row['topic']]['gene'] = row['gene']
        topics_dict_pytrec_eval[row['topic']]['demographic'] = row['demographic']
    return(topics_dict_pytrec_eval)

# FIXME: Remove weird things like "amplification, etc..." which give a worse score
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
    return(topics_df)

def get_qrels(qrel_file):
    assert os.path.exists(qrel_file)
    with open(qrel_file, 'r') as f_qrel:
        qrels = pytrec_eval.parse_qrel(f_qrel)
    return(qrels)

def run(run_id, topics_df):
    
    topics_dict = topics_to_pytrec_eval(topics_df)
    
    run_tuples_list = []
    
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
            row_tuple = topic_num, "Q0", hit["_id"], rank, hit["_score"], run_id
            run_tuples_list.append(row_tuple)
            rank = rank + 1

    return(pandas.DataFrame(columns=['TOPIC_NO','Q0','ID','RANK','SCORE','RUN_NAME'], data=run_tuples_list))

def evaluate(qrels, run, aggregated_measures={'ndcg':'', 'Rprec':'', 'P_10':''}):
    MEASURES_AGGREGATED = aggregated_measures

    evaluator = pytrec_eval.RelevanceEvaluator(qrels, pytrec_eval.supported_measures)
    results = evaluator.evaluate(run_to_pytrec_eval(run))

    for measure in MEASURES_AGGREGATED.keys():
        measure_all = pytrec_eval.compute_aggregated_measure(measure, [MEASURES_AGGREGATED[measure] for MEASURES_AGGREGATED in results.values()])
        MEASURES_AGGREGATED[measure] = round(measure_all, 4)
    
    return(MEASURES_AGGREGATED)