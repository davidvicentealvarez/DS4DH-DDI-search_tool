import os
import json
import os
import time
import urllib
from io import BytesIO
from pathlib import Path, PureWindowsPath, PurePosixPath

from flask import Flask, Blueprint, render_template, redirect, send_from_directory, send_file, url_for, request
# from flask_nav.elements import *
from markupsafe import Markup
from openpyxl import load_workbook
from werkzeug.utils import secure_filename

from elastic_query import search_document, get_document, search_chunk
from excel_writer import generate_log
from file_extractor import load_files_database
from settings import DRIVE_PATH, ES_INDEX_CHUNK_MAME, PREFIX_PATH


app = Flask(__name__, static_url_path="{}/static".format(PREFIX_PATH))


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
@app.route('{}/favicon.ico'.format(PREFIX_PATH))
def favicon():
    return redirect(url_for('static', filename='media/favicon.png'))


@app.route("{}/".format(PREFIX_PATH), methods=['GET', 'POST'])
def get_index():
    return redirect(url_for("get_home"))


@app.route("/ddi/home".format(PREFIX_PATH), methods=['GET', 'POST'])
def get_home():
    return render_template("home.html", page="Home", prefix=PREFIX_PATH)


@app.route("{}/help".format(PREFIX_PATH), methods=['GET', 'POST'])
def get_help():
    return render_template("help.html", page="Help", prefix=PREFIX_PATH)


@app.route("{}/search".format(PREFIX_PATH), methods=['GET', 'POST'])
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
                               page="Search", drive_path=DRIVE_PATH, prefix=PREFIX_PATH)
    return render_template("search_form.html", page="Search", drive_path=DRIVE_PATH, prefix=PREFIX_PATH)


@app.route("{}/analyze".format(PREFIX_PATH), methods=['GET', 'POST'])
def analyze():
    countries = sorted(os.listdir(Path(PureWindowsPath(DRIVE_PATH))), key=str.casefold)
    if request.method == "POST":
        query = request.form.get("query")
        filepaths = request.form.get("filepaths")
        language = request.form.get("language")
        return redirect(url_for("analyze_result", query=query, filepaths=filepaths, language=language))
    return render_template("analyze_form.html", page="Analyze", countries=countries, drive_path=DRIVE_PATH, prefix=PREFIX_PATH)


@app.route("{}/analyze/results".format(PREFIX_PATH), methods=['GET'])
def analyze_result():
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
    return render_template("analyze_result.html", page="Analyze", result=result, query=query,
                           keywords=keywords, drive_path=DRIVE_PATH, prefix=PREFIX_PATH)


@app.route("{}/file".format(PREFIX_PATH), methods=['GET'])
def get_file():
    path = urllib.parse.unquote(request.args.get("path"))
    path = Path(PureWindowsPath(path))
    embed = request.args.get("embed", type=str)
    if embed and embed == "True":
        as_attachment = False
    else:
        as_attachment = True
    return send_from_directory(path.parent.absolute().as_posix(), path.name, as_attachment=as_attachment)


@app.route("{}/directory/<dir_name>".format(PREFIX_PATH), methods=['POST'])
def add_dir(dir_name):
    dir_name = urllib.parse.unquote(dir_name)
    path = Path(PureWindowsPath(os.path.join(DRIVE_PATH, dir_name)))
    if not path.exists() or not path.is_dir():
        os.makedirs(path.absolute(), exist_ok=True)
    return ""


@app.route("{}/chunk/<id>".format(PREFIX_PATH), methods=['GET'])
def get_chunk(id):
    return get_document(ES_INDEX_CHUNK_MAME, id)


@app.route("{}/chunk/search".format(PREFIX_PATH), methods=['POST'])
def get_chunks():
    if request.mimetype != "application/json":
        return "No header set or wrong header for content-type. The payload must be in JSON", 415
    _input = request.json
    result = search_chunk(_input["filepath"], _input["keywords"])
    return result


@app.route("{}/upload".format(PREFIX_PATH), methods=["GET", "POST"])
def get_upload_page():
    countries = sorted(os.listdir(Path(PureWindowsPath(DRIVE_PATH))), key=str.casefold)
    report = dict()
    if request.method == "POST":
        report = upload_files()
    return render_template("upload_file.html", page="Upload", countries=countries, report=report,
                           drive_path=DRIVE_PATH, prefix=PREFIX_PATH)


@app.route("{}/upload-files".format(PREFIX_PATH), methods=["POST"])
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


@app.route("{}/log".format(PREFIX_PATH), methods=["POST"])
def build_log():
    if request.mimetype != "application/json":
        return "No header set or wrong header for content-type. The payload must be in JSON", 415
    data = request.json
    mem = generate_log(data)
    return send_file(mem, as_attachment=True, download_name="log.xlsx")


if __name__ == "__main__":
    # app1 = Flask(__name__, static_url_path="/ddi/static")




    # app1.register_blueprint(app, url_prefix="/ddi")


    app.run(debug=True, port=8901, host="0.0.0.0")
