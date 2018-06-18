#!/bin/bash
python query.py > test/all.2017.trec_eval
./trec_eval -m ndcg -m Rprec -m P test/all.2017.qrels test/all.2017.trec_eval | grep 'Rprec\|P_10\s\|ndcg'
