import logging

import PyPDF2
import json
from elasticsearch import Elasticsearch
import os
from pathlib import Path, PureWindowsPath, PurePosixPath
from tqdm import tqdm
import pandas as pd
import re
# from docx import Document
import docx2txt
# import module
import traceback
from elastic_query import is_document_indexed
from settings import ES_HOST, ES_PORT, ES_CERT_PATH, ES_USER, ES_PWD, DRIVE_PATH, ES_INDEX_CHUNK_MAME, ES_INDEX_DOC_MAME, ES_SCHEME, DRIVE_DIR_NAME

# es = Elasticsearch(ES_HOST + ":" + ES_PORT, ca_certs=ES_CERT_PATH,
#                    basic_auth=(ES_USER, ES_PWD))

es = Elasticsearch([f'{ES_SCHEME}://{ES_USER}:{ES_PWD}@{ES_HOST}:{ES_PORT}'])


class TextFileExtractor:
    new_line_pattern = re.compile(r"([\s]*\r\n[\s]*)")
    space_pattern = re.compile(r"[^\S\r\n]{2,}")
    sentence_pattern = re.compile(r"\.|\r\n|\n")

    def __init__(self):
        self.blob_pipelines = {
            ".pdf": self.get_pdf_text_blob,
            ".xlsx": self.get_xlsx_text_blob,
            ".xls": self.get_xls_text_blob,
            ".csv": self.get_csv_text_blob,
            ".txt": self.get_txt_text_blob,
            ".docx": self.get_docx_text_blob
        }

        self.chunk_pipelines = {
            ".pdf": self.get_pdf_text_chunks,
            ".xlsx": self.get_xlsx_text_chunks,
            ".xls": self.get_xls_text_chunks,
            ".csv": self.get_csv_text_chunks,
            ".txt": self.get_txt_text_chunks,
            ".docx": self.get_docx_text_chunks
        }

    def __format_chunks(self, sentences: list, page_num=0, chunk_num=0):
        text_chunks = list()
        chunk = ""
        while sentences:
            while len(chunk) < 1500 and sentences:
                chunk = chunk + " " + sentences.pop(0).rstrip()
            if len(chunk) > 2000:
                words = chunk.split()
                sub_chunk1 = ""
                sub_chunk2 = ""
                while len(sub_chunk1) < len(chunk) // 2:
                    sub_chunk1 = sub_chunk1 + " " + words.pop(0)
                while words:
                    sub_chunk2 = sub_chunk2 + " " + words.pop(0)
                text_chunks.append(
                    {"text": sub_chunk1, "page": page_num, "chunk": chunk_num, "length": len(sub_chunk1)})
                chunk_num += 1
                text_chunks.append(
                    {"text": sub_chunk2, "page": page_num, "chunk": chunk_num, "length": len(sub_chunk2)})
            elif len(chunk) > 200 or len(text_chunks) == 0:
                text_chunks.append({"text": chunk, "page": page_num, "chunk": chunk_num, "length": len(chunk)})
            else:
                text_chunks[-1]["text"] = text_chunks[-1]["text"] + " " + chunk
            chunk = ""
            chunk_num += 1
        return text_chunks, chunk_num

    def get_pdf_text_chunks(self, filepath):
        blob = {"meta": {}, "chunks": []}
        try:
            read_pdf = PyPDF2.PdfReader(filepath)
            chunk_num = 0
            page_num = 0
            for page in read_pdf.pages:
                text_data = page.extract_text()
                text_data = TextFileExtractor.new_line_pattern.sub("\n", text_data)
                text_data = TextFileExtractor.space_pattern.sub(" ", text_data)
                sentences = TextFileExtractor.sentence_pattern.split(text_data)
                text_chunks, chunk_num = self.__format_chunks(sentences, page_num, chunk_num)
                blob["chunks"].extend(text_chunks)
                page_num += 1
        except:
            pass
        return blob

    def get_pdf_text_blob(self, filepath):
        blob = {"meta": {}, "text_blob": ""}
        try:
            read_pdf = PyPDF2.PdfReader(filepath)
            pages = []
            for page in read_pdf.pages:
                text_data = page.extract_text()
                text_data = TextFileExtractor.new_line_pattern.sub("\n", text_data)
                text_data = TextFileExtractor.space_pattern.sub(" ", text_data)
                pages.append(text_data)
            blob["text_blob"] = " ".join(pages)
        except:
            pass
        return blob

    def get_xlsx_text_blob(self, filepath):
        blob = {"meta": {}, "text_blob": ""}
        texts = list()
        df_dict = pd.read_excel(filepath, sheet_name=None)
        for key in df_dict:
            df = df_dict[key]
            df.fillna("", inplace=True)
            df = df.astype(str)
            data = df.to_numpy().flatten().tolist()
            texts.extend(data)
        while ("" in texts):
            texts.remove("")
        blob["text_blob"] = " ".join(texts)
        return blob

    def get_xlsx_text_chunks(self, filepath):
        blob = {"meta": {}, "chunks": []}
        df_dict = pd.read_excel(filepath, sheet_name=None)
        page = 0
        for key in df_dict:
            df = df_dict[key]
            df.fillna("", inplace=True)
            df = df.astype(str)
            data = df.to_numpy().flatten().tolist()
            text_chunks, _ = self.__format_chunks(data, page)
            blob["chunks"].extend(text_chunks)

            page += 1
        return blob

    def get_xls_text_blob(self, filepath):
        return self.get_xlsx_text_blob(filepath)

    def get_xls_text_chunks(self, filepath):
        return self.get_xlsx_text_chunks(filepath)

    def get_csv_text_blob(self, filepath):
        blob = {"meta": {}, "text_blob": ""}
        df = pd.read_csv(filepath, sep=";")
        df.fillna("", inplace=True)
        df = df.astype(str)
        data = df.to_numpy().flatten().tolist()
        while ("" in data):
            data.remove("")
        blob["text_blob"] = " ".join(data)
        return blob

    def get_csv_text_chunks(self, filepath):
        blob = {"meta": {}, "chunks": []}
        df = pd.read_csv(filepath, sep=";")
        df.fillna("", inplace=True)
        df = df.astype(str)
        data = df.to_numpy().flatten().tolist()
        while ("" in data):
            data.remove("")
        text_chunks, _ = self.__format_chunks(data)
        blob["chunks"] = text_chunks
        return blob

    def get_txt_text_blob(self, filepath):
        blob = {"meta": {}, "text_blob": ""}
        data = list()
        with open(filepath) as fp:
            for line in fp:
                data.append(line.rstrip())
        while ("" in data):
            data.remove("")
        blob["text_blob"] = " ".join(data)
        return blob

    def get_txt_text_chunks(self, filepath):
        blob = {"meta": {}, "chunks": []}
        data = list()
        with open(filepath) as fp:
            for line in fp:
                line = line.rstrip()
                sentences = TextFileExtractor.sentence_pattern.split(line)
                data.extend(sentences)
        while ("" in data):
            data.remove("")
        text_chunks, _ = self.__format_chunks(data)
        blob["chunks"] = text_chunks
        return blob

    def get_doc_text_blob(self, filepath):
        raise NotImplemented
        # blob = {"meta": {}, "text_blob": ""}
        # text = textract.process(filepath)
        # data = " ".join(text.split())
        # blob["text_blob"] = data
        # return blob

    def get_doc_text_chunks(self, filepath):
        raise NotImplemented

    def get_docx_text_blob(self, filepath):
        blob = {"meta": {}, "text_blob": ""}
        data = docx2txt.process(filepath)
        data = " ".join(data.split())
        blob["text_blob"] = data
        return blob

    def get_docx_text_chunks(self, filepath):
        blob = {"meta": {}, "chunks": []}
        data = docx2txt.process(filepath)
        sentences = TextFileExtractor.sentence_pattern.split(data)
        text_chunks, _ = self.__format_chunks(sentences)
        blob["chunks"] = text_chunks
        return blob

    def __get_texts(self, path, full=True):
        file_extension = path.suffix
        if full:
            pipeline = self.blob_pipelines.get(file_extension, None)
        else:
            pipeline = self.chunk_pipelines.get(file_extension, None)
        if pipeline is not None:
            blob = pipeline(str(path))
            blob["filename"] = path.name
            blob["filepath"] = str(PureWindowsPath(path)).replace("D:\\WG_questions", "..")
            blob["filetype"] = str(file_extension).replace(".", "")
            parents = [p.name for p in path.parents]
            blob["country"] = parents[parents.index(DRIVE_DIR_NAME) - 1]
            return blob
        return None

    def get_blob(self, path):
        return self.__get_texts(path)

    def get_chunks(self, path):
        return self.__get_texts(path, False)


def get_filenames(dir):
    filepath_list = list()
    for (dirpath, dirnames, filenames) in os.walk(dir):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            filepath_list.append(filepath)
    return filepath_list


def load_full_file_database(path: Path):
    extractor = TextFileExtractor()
    blob = extractor.get_blob(path)
    if not blob:
        return "this extension is not supported."
    if not blob["text_blob"]:
        return "Couldn't extract any text, the body is empty."
    if not is_document_indexed(blob["filepath"], index=ES_INDEX_DOC_MAME):
        es.index(document=blob, index=ES_INDEX_DOC_MAME)
    return None


def load_chunks_file_database(path: Path):
    extractor = TextFileExtractor()
    blob = extractor.get_chunks(path)
    if not blob:
        return "This file extension/format is not supported"
    if not blob["chunks"]:
        return "Couldn't extract any text, the body is empty"
    blob["chunks"] = [i for i in blob["chunks"] if i["text"].rstrip()]
    if not is_document_indexed(blob["filepath"], index=ES_INDEX_CHUNK_MAME):
        bulk = []
        for chunk in blob["chunks"]:
            chunk["filename"] = blob["filename"]
            chunk["filepath"] = blob["filepath"]
            chunk["filetype"] = blob["filetype"]
            chunk["country"] = blob["country"]
            bulk.append({"index": {"_index": ES_INDEX_CHUNK_MAME}})
            bulk.append(chunk)
        es.bulk(index=ES_INDEX_CHUNK_MAME, operations=bulk)
    return None


def load_files_database(full: bool, filenames=None):
    errors = dict()
    success = list()
    # get_file_stat("../drive/Questionnaires")
    if not filenames:
        filenames = get_filenames(DRIVE_PATH)
    for filename in tqdm(filenames):
        path = PureWindowsPath(PurePosixPath(filename))
        path = Path(path)
        print(str(path))
        if full:
            error = load_full_file_database(path)

        else:
            error = load_chunks_file_database(path)
        if error:
            errors[filename] = error
        else:
            success.append(filename)
    return errors, success


def get_file_stat(dir):
    extensions = dict()
    filenames = get_filenames(dir)
    for filename in tqdm(filenames):

        path = Path(str(PureWindowsPath(PurePosixPath(filename))))
        if path.is_file():
            file_extension = path.suffix
            if file_extension not in extensions:
                extensions[file_extension] = 0
            extensions[file_extension] += 1
    print(extensions)


files_ext = {'.zip': 54, '.pdf': 2801, '.xlsx': 168, '.xls': 57, '.docx': 39, '.gz': 7, '.doc': 65, '.csv': 2,
             '.css': 8, '.download': 3, '.download(1)': 3, '.rar': 6, '.PDF': 3, '.JPG': 1, '.txt': 1}

if __name__ == "__main__":
    filenames = get_filenames("D:\WG_questions\drive\HFPS Questionnaires")
    # print(filenames[0])
    # filenames = [r"D:\WG_questions\drive\HFPS Questionnaires\Kenya\COVID-19 Rapid Response Phone Survey Waves 1-8 2020-2022\Copy of RRPS_rrps_w8_sctoform.xlsx"]
    # filenames = [r"D:\WG_questions\drive\HFPS Questionnaires\Uganda\COVID-19 HFPS 2020\Copy of Round 2 questionnaire.xlsx"]
    print(load_files_database(True, filenames))
    # print(get_xlsx_text_blob("D:\\WG_questions\\drive\\Questionnaires\\Belgium_\\SILC2020 - Individual questionnaire.xlsx"))
    # print(get_xlsx_text_blob("D:\\WG_questions\\drive\\Questionnaires\\Brazil\\Brazil dicionario_PNS_microdados_2019.xls"))
    # print(get_csv_text_blob("D:\\WG_questions\\drive\\Questionnaires\\Belgium_\\Household Budget Survey 2020\\Individual questionnaire.csv"))
    # print(get_txt_text_blob( "D:\\WG_questions\\drive\\Questionnaires\\South Sudan\\SSD_2015_HFS-W1_v01_M\\hfsss_w1_read_me.txt"))
    # print(extractor.get_doc_text_blob("D:\\WG_questions\\drive\\Questionnaires\\Belgium_\\SILC 2012\\SILC_2012 household.doc"))
    # print(
    # get_docx_text_blob2("D:\\WG_questions\\drive\\Questionnaires\\Belgium_\\SILC 2012\\SILC_2012 individual.docx"))
