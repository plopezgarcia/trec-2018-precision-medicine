import pandas
import json
import requests
from datetime import datetime
from trec_utils import utils, evaluation

config = utils.load_config()

URL_ABSTRACTS = config['ELASTIC'] + config['ABSTRACTS'] + '/_search'
URL_TRIALS = config['ELASTIC'] + config['TRIALS'] + '/_search'
HEADERS = {'Content-type': 'application/json'}

def get_default_run_params():
    return(default_run_params)

def replace_topic_dimensions(query, topic_row, topic_dimensions):
    for topic_dimension in topic_dimensions:
        query = query.replace('{{'+topic_dimension+'}}', topic_row[topic_dimension])
    return query

def replace_run_parameters(query, run_params, run_params_replaced):
    for run_parameter in run_params_replaced:
        if run_parameter in run_params:
            query = query.replace('{{'+run_parameter+'}}', str(run_params[run_parameter]))
    return query

example_run_params = {
    'run_id':'DEFAULT_RUN',
    'query_template':'baseline.json',
    'disease_tie_breaker':0.5,
    'disease_multi_match_type':'best_fields',
    'disease_boost':1.5,
    'gene_tie_breaker':0.5,
    'gene_multi_match_type':'cross_fields',
    'gene_boost':1
}

# abstracts_or_trials: 'ABSTRACTS', 'TRIALS'
def run(topics_df, abstracts_or_trials, run_params):

    run_id = run_params['run_id']
    run_tuples_list = []

    #print('RUN:', run_id, "TOPICS:", len(topics_df), run_params)
    print('RUN:', run_id, "TOPICS:", len(topics_df))

    for index, topic_row in topics_df.iterrows():

        #print("TOPIC:", topic_row['topic'])
        # Fill template with query
        with open('./query-templates/' + run_params['query_template'], 'r') as template_file:
            query = template_file.read()
            query = replace_topic_dimensions(query, topic_row, ['disease', 'gene', 'gene1', 'gene2', \
                                                                'sex', 'age', 'age_group'])
            query = replace_run_parameters(query, run_params,
                                            ['disease_tie_breaker','disease_multi_match_type', 'disease_boost', \
                                            'gene_tie_breaker', 'gene_multi_match_type', 'gene_boost'])
        #print(query)
        if abstracts_or_trials == 'ABSTRACTS':
            response = requests.post(URL_ABSTRACTS, data=query, headers=HEADERS)
        if abstracts_or_trials == 'TRIALS':
            response = requests.post(URL_TRIALS, data=query, headers=HEADERS)

        rank = 1
        for hit in response.json()["hits"]["hits"]:
            row_tuple = topic_row['topic'], "Q0", hit["_id"], rank, hit["_score"], run_id, \
                        hit["_source"]["title"]
            run_tuples_list.append(row_tuple)
            rank = rank + 1

    results = pandas.DataFrame(columns=['TOPIC_NO','Q0','ID','RANK','SCORE','RUN_NAME', 'TITLE'], data=run_tuples_list)

    return(results, run_params)


example_params_grid = {
    'query_template':['variable/baseline_sex_age.json'],
    'disease_tie_breaker':[0.0,0.2,0.5,0.7,1],
    'disease_multi_match_type':['best_fields', 'most_fields', 'cross_fields', 'phrase', 'phrase_prefix'],
    'disease_boost':[0.5,1,1.5,2],
    'gene_tie_breaker':[0.0,0.2,0.5,0.7,1],
    'gene_multi_match_type':['best_fields', 'most_fields', 'cross_fields', 'phrase', 'phrase_prefix'],
    'gene_boost':[0.5,1,1.5,2]
}

def experiment(topics_df, qrels_df, abstracts_or_trials, params_grid):
    run_number = 1
    print("EXPERIMENT BEGIN:", str(datetime.now()))
    print("RUNS:",  len(params_grid['query_template']) * \
                    len(params_grid['disease_tie_breaker']) * \
                    len(params_grid['disease_multi_match_type']) * \
                    len(params_grid['disease_boost']) * \
                    len(params_grid['gene_tie_breaker']) * \
                    len(params_grid['gene_multi_match_type']) * \
                    len(params_grid['gene_boost']))
    #print("PARAMS GRID:", params_grid)
    run_tuples_list = []
    for qt in params_grid['query_template']:
        for dtb in params_grid['disease_tie_breaker']:
            for dmmt in params_grid['disease_multi_match_type']:
                for db in params_grid['disease_boost']:
                    for gtb in params_grid['gene_tie_breaker']:
                        for gmmt in params_grid['gene_multi_match_type']:
                            for gb in params_grid['gene_boost']:
                                params = {
                                    'run_id':'-'.join([qt, str(dtb), str(dmmt), str(db), str(gtb), str(gmmt), str(gb)]),
                                    'query_template':qt,
                                    'disease_tie_breaker':str(dtb),
                                    'disease_multi_match_type':dmmt,
                                    'disease_boost':str(db),
                                    'gene_tie_breaker':str(gtb),
                                    'gene_multi_match_type':gmmt,
                                    'gene_boost':str(gb)
                                }
                                print(run_number)
                                run_df, run_params_df = run(topics_df, abstracts_or_trials, params)
                                results, aggregated = evaluation.evaluate(qrels_df, run_df)

                                row_tuple = qt, aggregated['ndcg'], aggregated['P_10'], aggregated['Rprec'], \
                                            str(dtb), dmmt, str(db), str(gtb), gmmt, str(gb)

                                run_tuples_list.append(row_tuple)
                                print(row_tuple)
                                run_number = run_number + 1

    results = pandas.DataFrame(columns=['template', 'ndcg', 'P_10', 'Rprec', 'dis_tb', 'dis_mm_type', 'dis_b', 'gene_tb', 'gene_mm_type', 'gene_b'], data=run_tuples_list)
    print("EXPERIMENT END:", str(datetime.now()))
    return(results.sort_values(['ndcg', 'P_10', 'Rprec'], ascending=[0, 0, 0]))
