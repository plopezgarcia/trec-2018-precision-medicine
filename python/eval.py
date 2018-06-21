import os
import xml.etree.ElementTree
import pytrec_eval
import pandas
import requests
import json
import re

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

# FIXME: Remove weird things like "amplification, etc..." which give a worse score
def get_topics(topics_file):
    input_topics = xml.etree.ElementTree.parse(topics_file).getroot().findall('topic')
    topics_dict = {}
    for t in input_topics:
        topic = int(float(t.get('number')))
        disease = t.find('disease').text
        gene = t.find('gene').text
        demographic = t.find('demographic').text
        gene_list = gene.split(',')
        gene1 = gene_list[0]
        gene2 = ''
        gene3 = '' 
        if (len(gene_list)>1):
            gene2 = gene_list[1]
        if (len(gene_list)>2):
            gene3 = gene_list[2]
        if 'female' in demographic:
            sex = 'female'
        else:
            sex = 'male'
        age = re.findall('\\d+',demographic)[0]
        
        topics_dict[topic] = {  'topic': topic,
                                'disease': disease,
                                'gene': gene,
                                'gene1': gene1,
                                'gene2': gene2,
                                'gene3': gene3,
                                'sex': sex,
                                'age': age}

    topics_df = pandas.DataFrame.from_dict(topics_dict, orient='index')
    topics_df  = topics_df [['topic', 'disease', 'gene',
                             'gene1', 'gene2', 'gene3', 'sex', 'age']]
    return(topics_df)

def get_qrels(qrel_file):
    assert os.path.exists(qrel_file)
    with open(qrel_file, 'r') as f_qrel:
        qrels = pytrec_eval.parse_qrel(f_qrel)
    return(qrels)




default_params = {
    'query_template':'baseline.json',
    'disease_tie_breaker':0.5,
    'disease_boost':1.5,
    'gene_tie_breaker':0.5,
    'gene_boost':1
}

def run(topics_df, params = default_params):

    run_id = "FIXME"
    run_tuples_list = []

    print('RUN:', run_id, params)

    for index, topic_row in topics_df.iterrows():
 
        # Fill template with query
        with open('./query-templates/' + params['query_template'], 'r') as template_file:
          query = template_file.read()
          query = query.replace('{{disease}}', topic_row['disease'])
          query = query.replace('{{gene}}', topic_row['gene'])

          query = query.replace('{{disease_tie_breaker}}', str(params['disease_tie_breaker']))
          query = query.replace('{{disease_boost}}', str(params['disease_tie_breaker']))
          query = query.replace('{{gene_tie_breaker}}', str(params['gene_tie_breaker']))
          query = query.replace('{{gene_boost}}', str(params['gene_boost']))

        response = requests.post(URL, data=query, headers=HEADERS)

        rank = 1
        for hit in response.json()["hits"]["hits"]:
            row_tuple = topic_row['topic'], "Q0", hit["_id"], rank, hit["_score"], run_id
            run_tuples_list.append(row_tuple)
            rank = rank + 1

    # Return also the query
    return(pandas.DataFrame(columns=['TOPIC_NO','Q0','ID','RANK','SCORE','RUN_NAME'], data=run_tuples_list))


def run2(topics_df, params = default_params):

    run_id = "FIXME"

    topics_dict = topics_to_pytrec_eval(topics_df)

    run_tuples_list = []

    print('RUN:', run_id, params)

    for topic_tuple in sorted(topics_dict.items()):
        topic_num = topic_tuple[0]
        topic = topic_tuple[1]
        #print('TOPIC:', topic['topic'], topic['disease'], topic['gene'], topic['demographic'], params)

        # For query...
        # Fill template with query
        with open('./query-templates/' + params['query_template'], 'r') as myfile:
          query = myfile.read()  #print(data)
          query = query.replace('{{disease}}', topic['disease'])
          query = query.replace('{{gene}}', topic['gene'])
          query = query.replace('{{demographic}}', topic['demographic'])

          query = query.replace('{{disease_tie_breaker}}', str(params['disease_tie_breaker']))
          query = query.replace('{{disease_boost}}', str(params['disease_tie_breaker']))
          query = query.replace('{{gene_tie_breaker}}', str(params['gene_tie_breaker']))
          query = query.replace('{{gene_boost}}', str(params['gene_boost']))

        response = requests.post(URL, data=query, headers=HEADERS)

        rank = 1
        for hit in response.json()["hits"]["hits"]:
            row_tuple = topic_num, "Q0", hit["_id"], rank, hit["_score"], run_id
            run_tuples_list.append(row_tuple)
            rank = rank + 1

    # Return also the query
    return(pandas.DataFrame(columns=['TOPIC_NO','Q0','ID','RANK','SCORE','RUN_NAME'], data=run_tuples_list))

def evaluate(qrels, run, aggregated_measures={'ndcg':'', 'Rprec':'', 'P_10':''}):
    MEASURES_AGGREGATED = aggregated_measures

    evaluator = pytrec_eval.RelevanceEvaluator(qrels, pytrec_eval.supported_measures)
    results = evaluator.evaluate(run_to_pytrec_eval(run))

    for measure in MEASURES_AGGREGATED.keys():
        measure_all = pytrec_eval.compute_aggregated_measure(measure, [MEASURES_AGGREGATED[measure] for MEASURES_AGGREGATED in results.values()])
        MEASURES_AGGREGATED[measure] = round(measure_all, 4)

    return(results, MEASURES_AGGREGATED)

default_params_grid = {
    'query_template':['variable.json'],
    'disease_tie_breaker':[0.1,0.5],
    'disease_boost':[1,2,5],
    'gene_tie_breaker':[0.1,0.5],
    'gene_boost':[1,2,5]
}

def experiment(topics_df, qrels, params_grid=default_params_grid):
    print(params_grid)
    for qt in params_grid['query_template']:
        for dtb in params_grid['disease_tie_breaker']:
            for db in params_grid['disease_boost']:
                for gtb in params_grid['gene_tie_breaker']:
                    for gb in params_grid['gene_boost']:
                        params = {
                            'query_template':qt,
                            'disease_tie_breaker':str(dtb),
                            'disease_boost':str(db),
                            'gene_tie_breaker':str(gtb),
                            'gene_boost':str(gb)
                        }
                        run_df = run(topics_df, params)
                        results, aggregated = evaluate(qrels, run_df)
                        print(aggregated)
