import os
import json
import xml.etree.ElementTree
import re
import pandas
import pytrec_eval
from sklearn.model_selection import train_test_split

def load_config():
    with open(os.path.dirname(__file__) + '/config.json', 'r') as f:
        return(json.load(f))

# Converts numerical age to MeSH age groups (adapted)
def to_age_group(years_of_age):
    age = int(years_of_age)
    if age < 2:
        return('newborn')
    if age < 12:
        return('child')
    if age < 18:
        return('adolescent')
    if age < 44:
        return('adult')
    return('aged')

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
                                'age': age,
                                'age_group': to_age_group(age)}

    topics_df = pandas.DataFrame.from_dict(topics_dict, orient='index')
    topics_df  = topics_df [['topic', 'disease', 'gene',
                             'gene1', 'gene2', 'gene3', 'sex', 'age', 'age_group']]
    return(topics_df)

def get_qrels_as_dict(qrel_file):
    assert os.path.exists(qrel_file)
    with open(qrel_file, 'r') as f_qrel:
        qrels = pytrec_eval.parse_qrel(f_qrel)
    return(qrels)

def get_qrels_as_df(qrels_file):
    qrels = get_qrels_as_dict(qrels_file)
    qrels_tuples_list = []
    for topic, doc_relevance in qrels.items():
        for doc, relevance in doc_relevance.items():
            qrels_tuples_list.append((int(topic), doc, int(relevance)))

    qrels_df = pandas.DataFrame(columns=['topic','doc_id','relev'], data=qrels_tuples_list)
    return(qrels_df.sort_values(['topic','relev'], ascending=[True, False]))

def get_qrels(qrels_file):
    return(get_qrels_as_df(qrels_file))

def run_to_pytrec_eval(df):
    run_dict_pytrec_eval = {}
    for index, row in df.iterrows():
        if str(row['TOPIC_NO']) not in run_dict_pytrec_eval.keys():
            run_dict_pytrec_eval[str(row['TOPIC_NO'])] = {}
        run_dict_pytrec_eval[str(row['TOPIC_NO'])][row['ID']] = row['SCORE']
    return(run_dict_pytrec_eval)

# To test that all functions work properly, run:
# eval.get_qrels_as_dict('./gold-standard/abstracts.2017.qrels') ==
# eval.qrels_to_pytrec_eval(eval.get_qrels_as_df(('./gold-standard/abstracts.2017.qrels')))

def qrels_to_pytrec_eval(qrels_df):
    qrels_dict = {}
    for index, qrel_row in qrels_df.iterrows():
        if str(qrel_row['topic']) not in qrels_dict:
            qrels_dict[str(qrel_row['topic'])] = {}
        qrels_dict[str(qrel_row['topic'])][qrel_row['doc_id']] = qrel_row['relev']
    return(qrels_dict)

def split_topics(topics_df, train_split=0.6, test_split=0.5):
    topics_train, topics_test_dev = train_test_split(topics_df, test_size=train_split)
    topics_test, topics_dev = train_test_split(topics_test_dev, test_size=test_split)
    return(topics_train, topics_test, topics_dev)

def qrels_of_topics(qrels, topics):
    return(qrels[(qrels['topic'].isin(topics['topic']))])

def split_qrels(qrels, topics_train, topics_test, topics_dev):
    return( qrels_of_topics(qrels, topics_train),
            qrels_of_topics(qrels, topics_test),
            qrels_of_topics(qrels, topics_dev))

def to_trec_run_file(run_df, run_params):
    run_df[['TOPIC_NO','Q0','ID','RANK','SCORE','RUN_NAME']].to_csv('submitted_runs/'+run_params['run_id'], \
                                                                    sep=' ', encoding='utf-8', \
                                                                    header=False, index=False)
