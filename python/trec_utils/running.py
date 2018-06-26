import pandas
import json
import requests

from trec_utils import utils, evaluation

config = utils.load_config()

URL = config['ELASTIC'] + config['ABSTRACTS'] + '/_search'
HEADERS = {'Content-type': 'application/json'}

default_run_params = {
    'query_template':'baseline.json',
    'disease_tie_breaker':0.5,
    'disease_boost':1.5,
    'gene_tie_breaker':0.5,
    'gene_boost':1
}

def get_default_run_params():
    return(default_run_params)

def run(topics_df, run_params = default_run_params):

    run_id = "FIXME"
    run_tuples_list = []

    print('RUN:', run_id, "TOPICS:", len(topics_df), run_params)

    for index, topic_row in topics_df.iterrows():

        #print("TOPIC:", topic_row['topic'])
        # Fill template with query
        with open('./query-templates/' + run_params['query_template'], 'r') as template_file:
          query = template_file.read()
          query = query.replace('{{disease}}', topic_row['disease'])
          query = query.replace('{{gene}}', topic_row['gene'])

          query = query.replace('{{disease_tie_breaker}}', str(run_params['disease_tie_breaker']))
          query = query.replace('{{disease_boost}}', str(run_params['disease_tie_breaker']))
          query = query.replace('{{gene_tie_breaker}}', str(run_params['gene_tie_breaker']))
          query = query.replace('{{gene_boost}}', str(run_params['gene_boost']))

        response = requests.post(URL, data=query, headers=HEADERS)

        rank = 1
        for hit in response.json()["hits"]["hits"]:
            row_tuple = topic_row['topic'], "Q0", hit["_id"], rank, hit["_score"], run_id, \
                        hit["_source"]["title"]
            run_tuples_list.append(row_tuple)
            rank = rank + 1

    results = pandas.DataFrame(columns=['TOPIC_NO','Q0','ID','RANK','SCORE','RUN_NAME', 'TITLE'], data=run_tuples_list)

    return(results, run_params)



default_params_grid = {
    'query_template':['variable.json'],
    'disease_tie_breaker':[0.1,0.5],
    'disease_boost':[1,2,5],
    'gene_tie_breaker':[0.1,0.5],
    'gene_boost':[1,2,5]
}

def experiment(topics_df, qrels_df, params_grid=default_params_grid):
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
                        run_df, run_params_df = run(topics_df, params)
                        results, aggregated = evaluation.evaluate(qrels_df, run_df)
                        print(aggregated)
