import os

import numpy as np
from elasticsearch import Elasticsearch
from elasticsearch import ApiError
from elastic_query import search_document
from settings import ES_HOST, ES_PORT, ES_CERT_PATH, ES_USER, ES_PWD, ES_INDEX_DOC_MAME, ES_INDEX_CHUNK_MAME, DRIVE_PATH
import json
import itertools
import pandas as pd
import traceback
from tqdm import tqdm
from trectools import TrecQrel, TrecRun, TrecEval
es = Elasticsearch(ES_HOST+":"+ES_PORT)


def get_positive_data(filepath: str):
    df = pd.read_excel(filepath, sheet_name=0,
                       dtype={"Country": str, "Dataset": str, "Year": str, "Language":str, "Filepath": str, "seeing": int,
                              "hearing": int, "walking": int, "cognition": int, "selfcare": int, "communication": int,
                              "Exact": int, "Remarks": str,

                              })
    df.dropna(subset="Filepath", inplace=True)
    return df


def build_queries():
    with open("static/media/terms_eng.json") as fp:
        data = json.load(fp)
    keywords = data["fuzzy"]
    keys = list(keywords.keys())
    queries = dict()
    query_id = 0
    combinations = list(itertools.product([0, 1], repeat=6))
    for combination in combinations:
        item = dict()
        for i in range(len(combination)):
            if combination[i]:
                item[keys[i]] = keywords[keys[i]]
        queries[query_id] = {"query":item, "bit_vector": combination}
        query_id += 1
    del queries[0]
    with open("eval/queries.json", "w") as fp:
        json.dump(queries, fp, indent=4)


def get_elasticsearch_ids(df):
    es_id_list = list()
    for row in df.itertuples():
        filepath = row.Filepath
        filepath = filepath.replace(r"D:\WG_questions", "..")
        result = es.search(query={"match": {"filepath.keyword": filepath}}, source=False, index=ES_INDEX_DOC_MAME)
        if result["hits"]["total"]["value"] == 1:
            es_id_list.append(result["hits"]["hits"][0]["_id"])
        else:
            es_id_list.append(None)
    return es_id_list


def build_qrel():
    df = get_positive_data(r"D:\WG_questions\files.xlsx")
    es_ids = get_elasticsearch_ids(df)
    df = df.assign(Elasticsearch_id=es_ids)
    df = df[df["Language"] == "ENG"]
    df.dropna(subset="Elasticsearch_id", inplace=True)
    with open("eval/queries.json") as fp:
        queries = json.load(fp)
    with open("eval/ddi_qrel.txt", "w") as fp:
        for query in queries:
            for row in df.itertuples():
                query_vector = np.array(queries[query]["bit_vector"])
                label_vector = np.array([row.seeing, row.hearing, row.walking, row.cognition, row.selfcare, row.communication])
                if (label_vector * query_vector).sum() == query_vector.sum():
                    fp.write(str(query)+" 0 "+row.Elasticsearch_id+" 1\n")


def build_run_dict(TrecRun_path, depth) -> dict:
    """
    Builds a dictionary from the result. Each key is the query ID, and the value is a set of codes that were retrieved by the ontology mapper for that query.
    Args:
        TrecRun_path: The location of the trec result file
        depth: Number of results/codes to consider in the evaluation for each query

    Returns:
        the computed dictionary

    """
    run = dict()
    with open(TrecRun_path) as fp_run:
        for line in fp_run:
            line = line.rstrip()
            query_id, _, doc_id, rank, score, run_name = line.split()
            rank = int(rank)
            if rank <= depth:
                if query_id not in run:
                    run[query_id] = set()
                run[query_id].add(doc_id)
    return run


def build_qrel_dict(TrecQrel_path) -> dict:
    """
    Builds a dictionary from the Qrel file. Each key is the query ID, and the value is a set of true/golden codes .
    Args:
        TrecQrel_path: The location of the Qrel file

    Returns:
        the computed dictionary

    """
    golden_labels = dict()
    with open(TrecQrel_path) as fp_qrel:
        for line in fp_qrel:
            line = line.rstrip()
            query_id, _, doc_id, relevance = line.split()
            if query_id not in golden_labels:
                golden_labels[query_id] = set()
            golden_labels[query_id].add(doc_id)
    return golden_labels


def recall_at_k(TrecRun_path, TrecQrel_path, depth=10) -> float:
    """
    Computes the recall at k (since it is not implemented it trectools). It first builds the result and qrel dict.
    Then for each query ID, it counts how many golden codes were present int the result set, divided by the number of golden codes
    Finally it computes the average of recall at K.
    Args:
        TrecRun_path: The location of the trec result file
        TrecQrel_path: The location of the Qrel file
        depth: Number of results/codes to consider in the evaluation for each query, 1 will compute recall at 1, 3 is recall at 3 etc.

    Returns: the average of the recall at k for the dataset

    """
    run = build_run_dict(TrecRun_path, depth)
    golden_labels = build_qrel_dict(TrecQrel_path)
    avg_recall = 0
    for query_id in golden_labels:
        if query_id in run:
            recall = len(golden_labels[query_id] & run[query_id]) / len(golden_labels[query_id])
        else:
            recall = 0
        avg_recall += recall
    return avg_recall / len(golden_labels.keys())


def create_result(run_name, query_fp):
    with open(query_fp) as fp:
        queries = json.load(fp)
    with open("eval/ddi_trecrun_"+run_name+".txt", "w") as fp:
        for key in queries:
            query = queries[key]["query"]
            result = search_document(query, size=1000)
            for i in range(len(result["hits"]["hits"])) :
                fp.write(key+" q0 "+result["hits"]["hits"][i]["_id"]+" "+str(i+1)+" "+str(result["hits"]["hits"][i]["_score"])+" "+run_name+"\n")

def evaluate_run(run_name, depth=10):
    qrel = TrecQrel("eval/ddi_qrel3.txt")
    run = TrecRun("eval/ddi_trecrun_"+run_name+".txt")
    eval = TrecEval(run, qrel)

    return eval.get_ndcg(depth=depth, per_query=True), eval.get_precision(depth=depth, per_query=True), recall_at_k("eval/ddi_trecrun_"+run_name+".txt", "eval/ddi_qrel3.txt",depth)


def update_index(b, k1, index=ES_INDEX_DOC_MAME):
    settings = {"index": {"similarity": {"default": {"type": "BM25"}}}}
    settings["index"]["similarity"]["default"]["b"] = b
    settings["index"]["similarity"]["default"]["k1"] = k1

    es.indices.close(index=index)
    es.indices.put_settings(index=index, settings=settings)
    es.indices.open(index=index)
    es.indices.refresh(index=index)


def fine_tune():
    k1_list = np.arange(100, 1000, 1).tolist()
    b_list = [0.5]
    parameters = dict()
    for k1 in tqdm(k1_list):
        for b in b_list:
            try:
                run_name= "fine_tune_b{:0.1f}_k{:0.1f}".format(b,k1)
                update_index(b, k1)
                create_result(run_name, "eval/queries.json")
                map_10, p_10, r_10 = evaluate_run(run_name)
                parameters["b{:0.1f}_k{:0.1f}".format(b,k1)] = {"MAP@10":map_10, "precision@10":p_10, "recall@10":r_10}
            except:
                traceback.print_exc()
                print(b, k1)
    parameters = {k: v for k, v in sorted(parameters.items(), key=lambda item: item[1]["MAP@10"] + item[1]["precision@10"] + item[1]["recall@10"], reverse=True)}
    with open("eval/result.json", "w") as fp:
        json.dump(parameters, fp, indent=4)


if __name__ == "__main__":
    update_index(0.5, 103)
    # k_list = [1, 5, 10]
    # for k in k_list:
    #     map_10, p_10, r_10 = evaluate_run("fine_tune_b{:0.1f}_k{:0.1f}".format(0.5,103), k)
    #     print(k, map_10, p_10, r_10)