import json

from elasticsearch import Elasticsearch
from elasticsearch import ApiError
from settings import ES_HOST, ES_PORT, ES_CERT_PATH, ES_USER, ES_PWD, ES_INDEX_DOC_MAME, ES_INDEX_CHUNK_MAME, DRIVE_PATH, ES_SCHEME

# es = Elasticsearch(ES_HOST+":"+ES_PORT, ca_certs=ES_CERT_PATH,
#                    basic_auth=(ES_USER, ES_PWD))

es = Elasticsearch([f'{ES_SCHEME}://{ES_USER}:{ES_PWD}@{ES_HOST}:{ES_PORT}'])


def search_document(query, index=ES_INDEX_DOC_MAME, size=10):
    body = {}
    if "any" in query:
        body["bool"] = {"should": []}
        for item in query["any"]:
            body["bool"]["should"].append({"match": {"text_blob": {"query": item}}})
    else:
        body["bool"] = {"must": []}
        for field in query:
            field_query = {"bool": {"should": []}}
            for item in query[field]:
                field_query["bool"]["should"].append({"match": {"text_blob": {"query": item}}})
            body["bool"]["must"].append(field_query)
    return es.search(query=body, index=index, source=["filepath", "filetype", "country"], size=size)


def search_chunk(document_name, keyword_list, index=ES_INDEX_CHUNK_MAME, source=True):
    body = {"bool": {"must": [{"match": {"filepath.keyword": {"query": document_name}}}]}}
    term_query = {"bool": {"should": []}}
    for keyword in keyword_list:
        term_query["bool"]["should"].append({"match": {"text": {"query": keyword}}})
    body["bool"]["must"].append(term_query)
    return es.search(query=body, index=index, size=100, source=source)["hits"]["hits"]


def is_document_indexed(windows_path, index=ES_INDEX_CHUNK_MAME):
    query = {"match":{"filepath.keyword": windows_path}}
    result = es.search(query=query, index=index, source=False)
    return len(result["hits"]["hits"]) > 0


def get_document(index, id):
    try:
        return es.get(index=index, id=id)["_source"]
    except ApiError as ex:
        return ex.info, ex.status_code


""""
{
  "query":{
    "bool": {
      "must":[
        {"bool": {"should": [{"match":{"text_blob":{"query": "deaf"}}}]}}
      ]
    }
  },
   "_source": false,
   "fields": ["filepath", "filetype", "country"]
}"""
