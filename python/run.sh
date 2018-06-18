python query.py > test/all.2017.trec_eval
./trec_eval test/all.2017.qrels test/all.2017.trec_eval | grep 'Rprec'
