import os
import xml.etree.ElementTree
import pytrec_eval
import pandas
    
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