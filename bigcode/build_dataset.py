import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
import os

def read_msg_from_file(self, file_name) -> str:
    input_text = ""
    fp = open(file_name, "r")
    while True:
        line = fp.readline()
        if not line:
            break
        input_text += line
    fp.close()
    assert(input_text != "")
    return input_text


ds_path1 = "/data/yanhr/mutation_range_source/"
ds_path2 = "/data/yanhr/mutation_insert_range/"

code_col = []
length_col = []
repo_name_col = []
path_col = []
language_col = []
license_col = []
dirs = os.listdir(ds_path1)
for dir in dirs:
    files = os.listdir(ds_path1 + dir + "/")
    for file in files:
        fp = open(ds_path1 + dir + "/" + file, "r")
        code = ""
        while True:
            line = fp.readline()
            if not line:
                break
            code += line
        code_col.append(code)
        length_col.append(len(code))
        repo_name_col.append("test")
        path_col.append(ds_path1 + dir + "/" + file)
        language_col.append("C")
        license_col.append("isc")

dirs = os.listdir(ds_path2)
for dir in dirs:
    files = os.listdir(ds_path2 + dir + "/")
    for file in files:
        fp = open(ds_path2 + dir + "/" + file, "r")
        code = ""
        while True:
            line = fp.readline()
            if not line:
                break
            code += line
        if "<mask>" in code or "<mask_ext>" in code:
            continue
        else:
            code_col.append(code)
            length_col.append(len(code))
            repo_name_col.append("test")
            path_col.append(ds_path2 + dir + "/" + file)
            language_col.append("C")
            license_col.append("isc")

df_tmp = {"code": code_col, 
          "repo_name": repo_name_col, 
          "path": path_col, 
          "language":language_col, 
          "license": license_col, 
          "size": length_col}

df = pd.DataFrame(df_tmp)

df.to_parquet(path="./test.parquet", compression=None, )