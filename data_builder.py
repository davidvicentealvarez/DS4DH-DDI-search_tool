import pandas as pd
from file_extractor import TextFileExtractor, get_filenames
from pathlib import Path, WindowsPath
from tqdm import tqdm
import os

def get_positive_data(filepath: str):
    df = pd.read_excel(filepath, sheet_name=0,
                       dtype={"Country": str, "Dataset": str, "Year(s)": str, "Filepath": str, "Seeing": int,
                              "Hearing": int, "Walking": int, "cognition": int, "self-care": int, "communication": int,
                              "Exact": int, "Remarks": str,

                              })
    df.dropna(subset="Filepath", inplace=True)
    return df


def get_data(filepath):
    positives_df = get_positive_data(filepath)
    countries = set()
    positives_filenames = set()
    text_pipeline = TextFileExtractor()
    blob_list = list()
    chunks_list = list()
    for row in tqdm(positives_df.itertuples()):
        countries.add(row.Filepath.split("\\")[4])
        positives_filenames.add(row.Filepath)
        path = Path(row.Filepath)
        blob = text_pipeline.get_blob(path)
        if blob and blob["text_blob"]:
            blob_list.append(blob["text_blob"])
        else:
            blob_list.append("")
        chunks = text_pipeline.get_chunks(path)
        if chunks and chunks["chunks"]:
            chunks_list.append(chunks["chunks"])
        else:
            chunks_list.append([])
    positives_df = positives_df.assign(text_blob=blob_list)
    positives_df = positives_df.assign(text_chunks=chunks_list)
    negative_data = list()
    filenames = list()
    for country in countries:
        filenames.extend(get_filenames(os.path.join(r"D:\WG_questions\drive\Questionnaires", country)))

    for filename in tqdm(filenames):
        if filename not in positives_filenames:
            blob = text_pipeline.get_blob(Path(filename))
            chunks = text_pipeline.get_chunks(Path(filename))
            if blob and blob["text_blob"] and not ("seeing" in blob["text_blob"] or "hearing" in blob["text_blob"] or "walking" in blob["text_blob"] or "cognition" in blob["text_blob"] or "self-care" in blob["text_blob"] or "communication" in blob["text_blob"]) :

                negative_data.append({"Country": country, "Dataset": None, "Year(s)": None, "Filepath": filename,
                                      "Seeing": 0, "Hearing": 0, "Walking": 0, "cognition": 0, "self-care": 0, "communication": 0,
                 "Exact": 0, "Remarks": None, "text_blob": blob, "text_chunks": chunks})
    negatives_df = pd.DataFrame(negative_data)
    print(len(negatives_df))
    return positives_df, negatives_df


if __name__ == "__main__":
    positives_df, negatives_df = get_data(r"D:\WG_questions\files.xlsx")
    with open("positives.json", "w") as fp:
        fp.write(positives_df.to_json(orient="records", indent=4))
    with open("negatives.json", "w") as fp:
        fp.write(negatives_df.to_json(orient="records", indent=4))
    # print(os.path.join(r"D:\WG_questions\drive\Questionnaires", "chile"))
