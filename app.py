import os
import json
import os
import time
import urllib
from io import BytesIO
from pathlib import Path, PureWindowsPath, PurePosixPath

from dominate.tags import img
from flask import Flask, render_template, redirect, send_from_directory, send_file
from flask_nav.elements import *
from markupsafe import Markup
from openpyxl import load_workbook
from werkzeug.utils import secure_filename

from elastic_query import search_document, get_document, search_chunk
from excel_writer import generate_log
from file_extractor import load_files_database
from settings import DRIVE_PATH, ES_INDEX_CHUNK_MAME

app = Flask(__name__)

logo = img(src='/static/media/favicon.png', height="40", width="126", style="margin-top:-15px")


@app.template_filter('urlencode')
def urlencode_filter(s):
    if type(s) == 'Markup':
        s = s.unescape()
    s = s.encode('utf8')
    s = urllib.parse.quote(s)
    return Markup(s)


##############################################
#         Render favicon page                #
##############################################
@app.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='media/favicon.png'))


@app.route("/", methods=['GET', 'POST'])
def get_index():
    return redirect(url_for('multi_search'))


@app.route("/search", methods=['GET', 'POST'])
def redirect_search():
    return redirect(url_for('multi_search'))


@app.route("/search-multi", methods=['GET', 'POST'])
def multi_search():
    if request.method == "POST":
        print(request.form.get("query"))
        query = json.loads(request.form.get("query"))
        result = search_document(query, size=request.form.get("size", default=10, type=int))
        max_score = result["hits"]["max_score"]
        for item in result["hits"]["hits"]:
            item["_score_rel"] = item["_score"] / max_score
        page = request.args.get("page", default=1, type=int)
        max_page = len(result["hits"]["hits"]) // 10
        if len(result["hits"]["hits"]) % 10 != 0:
            max_page += 1
        if page > max_page or page < 0:
            page = max_page
        if page == 0:
            page = 1
        return render_template("search_result.html", results=result["hits"]["hits"][(page - 1) * 10:page * 10],
                               page_number=page, max_page=max_page, terms_file=request.form.get("language"),
                               page="Search-multi", drive_path=DRIVE_PATH)
    return render_template("search_form.html", page="Search-multi", drive_path=DRIVE_PATH)


@app.route("/search-single", methods=['GET', 'POST'])
def single_search():
    countries = os.listdir(Path(PureWindowsPath(DRIVE_PATH)))
    if request.method == "POST":
        query = request.form.get("query")
        filepaths = request.form.get("filepaths")
        language = request.form.get("language")
        return redirect(url_for("single_search_result", query=query, filepaths=filepaths, language=language))
    return render_template("single_search.html", page="Search-single", countries=countries, drive_path=DRIVE_PATH)


@app.route("/search-single/results", methods=['GET'])
def single_search_result():
    query = json.loads(request.args.get("query"))
    filepaths = json.loads(request.args.get("filepaths"))
    language = request.args.get("language")
    time.sleep(3)
    result = dict()
    for filepath in filepaths:
        temp = search_chunk(filepath, query["any"], source=False)
        result[filepath] = [hit["_id"] for hit in temp]
    with open("." + language) as fp:
        stopwords = set(json.load(fp)["stopwords"])
    keywords = list()
    for keyword in query["any"]:
        keywords.append(' '.join([word for word in keyword.split() if word not in stopwords]))
    return render_template("single_search_result.html", page="Search-single", result=result, query=query,
                           keywords=keywords, drive_path=DRIVE_PATH)


@app.route("/file", methods=['GET'])
def get_file():
    path = urllib.parse.unquote(request.args.get("path"))
    path = Path(PureWindowsPath(path))
    embed = request.args.get("embed", type=str)
    if embed and embed == "True":
        as_attachment = False
    else:
        as_attachment = True
    return send_from_directory(path.parent.absolute().as_posix(), path.name, as_attachment=as_attachment)


@app.route("/directory/<dir_name>", methods=['POST'])
def add_dir(dir_name):
    dir_name = urllib.parse.unquote(dir_name)
    path = Path(PureWindowsPath(os.path.join(DRIVE_PATH, dir_name)))
    if not path.exists() or not path.is_dir():
        os.makedirs(path.absolute(), exist_ok=True)
    return ""


@app.route("/chunk/<id>", methods=['GET'])
def get_chunk(id):
    return get_document(ES_INDEX_CHUNK_MAME, id)


@app.route("/chunk/search", methods=['POST'])
def get_chunks():
    if request.mimetype != "application/json":
        return "No header set or wrong header for content-type. The payload must be in JSON", 415
    _input = request.json
    result = search_chunk(_input["filepath"], _input["keywords"])
    return result


@app.route("/upload-page", methods=["GET", "POST"])
def get_upload_page():
    countries = os.listdir(Path(PureWindowsPath(DRIVE_PATH)))
    report = dict()
    if request.method == "POST":
        report = upload_files()
    return render_template("upload_file.html", page="Upload", countries=countries, report=report, drive_path=DRIVE_PATH)


@app.route("/upload-files", methods=["POST"])
def upload_files():
    file_list = request.files.getlist("files")
    directory = request.form.get("country")
    filepaths = list()
    for file in file_list:
        filename = secure_filename(file.filename)
        filepath = os.path.join(DRIVE_PATH, directory, filename)
        filepath = str(PureWindowsPath(PurePosixPath(filepath)))
        filepaths.append(filepath)
        if not Path(filepath).exists():
            file.save(Path(PurePosixPath(PureWindowsPath(filepath))))
    report = {"full": {"errors": {}, "success": []}, "chunks": {"errors": {}, "success": []}}
    if filepaths:
        report["full"]["errors"], report["full"]["success"] = load_files_database(full=True, filenames=filepaths)
        report["chunks"]["errors"], report["chunks"]["success"] = load_files_database(full=False, filenames=filepaths)
    return report


@app.route("/log", methods=["POST"])
def build_log():
    if request.mimetype != "application/json":
        return "No header set or wrong header for content-type. The payload must be in JSON", 415
    data = request.json
    mem = generate_log(data)
    return send_file(mem, as_attachment=True, download_name="log.xlsx")


if __name__ == "__main__":
    app.run(debug=True, port=8900, host="0.0.0.0")
