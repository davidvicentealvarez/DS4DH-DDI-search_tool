import os
ES_INDEX_DOC_MAME = "disabilities_clean"
ES_INDEX_CHUNK_MAME = "disabilities_chunks_clean"
if "/app/src" in os.getcwd():
    ES_HOST = "elasticsearch_ddi"
else:
    ES_HOST = "localhost"
ES_PORT = "9800"
ES_SCHEME = "http"
ES_CERT_PATH = "certs/http_ca.crt"
ES_USER = "elastic"
ES_PWD = "" # UPDATE THIS
DRIVE_DIR_NAME = "Questionnaire_clean"
DRIVE_PATH = "..\\drive\\" + DRIVE_DIR_NAME
LOG_LEVEL= "DEBUG"
REVERSE_PROXY=True
if REVERSE_PROXY:
    PREFIX_PATH = "/ddi"
else:
    PREFIX_PATH = ""
