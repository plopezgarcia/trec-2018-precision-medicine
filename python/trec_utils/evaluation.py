import pytrec_eval
import pandas
import json
from trec_utils import utils

def evaluate(qrels, run, aggregated_measures={'recall_1000':'','ndcg':'', 'Rprec':'', 'P_10':''}):
    MEASURES_AGGREGATED = aggregated_measures

    evaluator = pytrec_eval.RelevanceEvaluator(utils.qrels_to_pytrec_eval(qrels), utils.pytrec_eval.supported_measures)
    results = evaluator.evaluate(utils.run_to_pytrec_eval(run))

    for measure in MEASURES_AGGREGATED.keys():
        measure_all = pytrec_eval.compute_aggregated_measure(measure, [MEASURES_AGGREGATED[measure] for MEASURES_AGGREGATED in results.values()])
        MEASURES_AGGREGATED[measure] = round(measure_all, 4)

    return(results, MEASURES_AGGREGATED)
