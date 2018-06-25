import sys
if sys.version_info < (3, 0):
    sys.stdout.write("Sorry, requires Python 3.x\n")
    sys.exit(1)

import os
import json
import requests
import xml.etree.ElementTree
import operator
import pytrec_eval

with open('config.json', 'r') as f:
    config = json.load(f)

ABSTRACTS_QRELS = './gold-standard/abstracts.2017.qrels'
# ABSTRACTS_RUNS = './test/all.2017.trec_eval'
#
assert os.path.exists(ABSTRACTS_QRELS)
# assert os.path.exists(ABSTRACTS_RUNS)
#
with open(ABSTRACTS_QRELS, 'r') as f_qrel:
    qrel = pytrec_eval.parse_qrel(f_qrel)
#
# with open(ABSTRACTS_RUNS, 'r') as f_run:
#     run = pytrec_eval.parse_run(f_run)
#
# print(run['30'])
# quit(0)
#
# evaluator = pytrec_eval.RelevanceEvaluator(qrel, pytrec_eval.supported_measures)
#
# results = evaluator.evaluate(run)
#
# def print_line(measure, scope, value):
#     print('{:25s}{:8s}{:.4f}'.format(measure, scope, value))
#
# rabo = ''
#
# print (results['30'])
# quit()
# for query_id, query_measures in sorted(results.items()):
#     print(query_measures['1'])
#     #for measure, value in sorted(query_measures.items()):
#     #   print_line(measure, query_id, value)
#     rabo = query_measures
#
# quit(0)
#
# for measure in sorted(query_measures.keys()):
#     print_line(
#         measure,
#         'all',
#         pytrec_eval.compute_aggregated_measure(
#             measure,
#             [query_measures[measure]
#              for query_measures in results.values()]))
#
# quit(0)

URL = config['ELASTIC'] + config['ABSTRACTS'] + '/_search'
HEADERS = {'Content-type': 'application/json'}

INPUT_TOPICS = xml.etree.ElementTree.parse('./topics/topics'+config['TOPICS_YEAR']+'.xml').getroot().findall('topic')

topics = {}
run = {}
run_output_file = []

for t in INPUT_TOPICS:

    # Read from file
    topic = int(float(t.get('number')))
    topics[topic] = {'topic': topic,
                    'disease': t.find('disease').text,
                    'gene': t.find('gene').text,
                    'demographic': t.find('demographic').text}

for topic_tuple in sorted(topics.items()):
    topic_num = topic_tuple[0]
    topic = topic_tuple[1]
    print("TOPIC:", str(topic_num))
    #print(topic['topic'], topic['disease'], topic['gene'], topic['demographic'])

    # For query...
    # Fill template with query
    with open('./query-templates/experimental1.json', 'r') as myfile:
      query = myfile.read()  #print(data)
      query = query.replace('{{disease}}', topic['disease'])
      query = query.replace('{{gene}}', topic['gene'])
      query = query.replace('{{demographic}}', topic['demographic'])
      #print(query)

    response = requests.post(URL, data=query, headers=HEADERS)
    #print(response.json())

    run_id = "my_run"
    rank = 1

    for hit in response.json()["hits"]["hits"]:
        #print(topic_num, "Q0", hit["_id"], rank, hit["_score"], run)

        #Build list to export to file
        row_tuple = str(topic_num), "Q0", hit["_id"], str(rank), str(hit["_score"]), run_id
        run_output_file.append(row_tuple)
        rank = rank + 1

        #Build structure for python trec_eval
        if str(topic_num) not in run.keys():
            run[str(topic_num)] = {}
        run[str(topic_num)][hit["_id"]] = hit["_score"]

MEASURES_AGGREGATED = {'ndcg':'', 'Rprec':'', 'P_10':''}

evaluator = pytrec_eval.RelevanceEvaluator(qrel, pytrec_eval.supported_measures)
results = evaluator.evaluate(run)

for measure in MEASURES_AGGREGATED.keys():
    measure_all = pytrec_eval.compute_aggregated_measure(measure, [MEASURES_AGGREGATED[measure] for MEASURES_AGGREGATED in results.values()])
    MEASURES_AGGREGATED[measure] = round(measure_all, 4)
    #print(measure, 'all', measure_all)

for row in run_output_file:
    print(" ".join(row))

print(MEASURES_AGGREGATED)

print()

quit()

with open('daemons.txt', 'w') as fp:
    fp.write('\n'.join('%s %s %s %s %s %s' % x for x in run_file))
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
