#!/home/wdjo224/miniconda3/envs/protein_binding/bin python

import argparse
import time
import dask.dataframe as dd
import pandas as pd
# try using pandas instead
from functools import reduce

parser = argparse.ArgumentParser(description="Process files containing protein binding affinity features")
parser.add_argument('--p', type=str, nargs='+', help="list paths of files containing protein features")
parser.add_argument('--pm', type=str, help="list paths of files containing protein-molecular compound features")
parser.add_argument('--m', type=str, help="file containing molecular descriptors")
parser.add_argument('--bp',type=str, help="file containing binding pocket features")
parser.add_argument('--feats', type=str, help="file containing which molecular descriptors to keep")
parser.add_argument('--out_dir',type=str,help="output directory to contain all generated files")
parser.add_argument('--o', type=str, help="name of the output file")
args = parser.parse_args()


def read_input_files():
    start_time = time.clock()
    protein_drug_features = []

    if args.pm is not None:
        t0 = time.time()
        protein_drug_features = load_features(args.pm, "receptor")
        pd.DataFrame(protein_drug_features.columns).to_csv(args.out_dir+"/binding_features.csv")
        t1 = time.time()
        print("binding features parsed in ", (t1 - t0), " seconds.")

    if args.p is not None:
        protein_data_list = []
        t0 = time.time()

        for path in args.p:
            df = load_features(path, "receptor")
            protein_data_list.append(df)

        protein_features = reduce(lambda x, y: pd.merge(x, y, left_index=True, right_index=True), protein_data_list)
        t1 = time.time()
        print("protein features parsed in ", (t1 - t0), " seconds.")
        pd.DataFrame(protein_features.columns).to_csv(args.out_dir+"/protein_features_list.csv")
        protein_drug_features = pd.merge(protein_drug_features, protein_features, left_index=True, right_index=True)

        del protein_features

    if args.bp is not None:
        t0 = time.time()
        binding_pocket_features = load_features(args.bp, "receptor")
        t1 = time.time()
        print("binding pocket features parsed in", (t1-t0), "seconds.")
        pd.DataFrame(binding_pocket_features.columns).to_csv(args.out_dir+"/pocket_features_list.csv")
        protein_drug_features = pd.merge(protein_drug_features,binding_pocket_features,left_index=True,right_index=True)

        del binding_pocket_features

    if args.m is not None:
        t0 = time.clock()
        drug_features = load_features(args.m, "drugID")
        protein_drug_features = protein_drug_features.reset_index()
        protein_drug_features = protein_drug_features.set_index('drugID')
        protein_drug_features = pd.merge(protein_drug_features, drug_features, left_index=True, right_index=True)

        t1 = time.clock()
        print("drug features parsed in ", (t1 - t0), " seconds.")
        pd.DataFrame(drug_features.columns).to_csv(args.out_dir+"/drug_features_list.csv")
        del drug_features

    output_file_name = args.o
    if output_file_name is None:
        output_file_name = "full_parser_output"
    protein_drug_features = protein_drug_features.reset_index()
    protein_drug_features = protein_drug_features.assign(label=protein_drug_features['drugID'].str.contains("active"))
    protein_drug_features['label'] = protein_drug_features['label'].astype(int)
    t0 = time.clock()
    protein_drug_features.to_csv(args.out_dir+"/"+str(output_file_name)+".csv", header=True, index=False)
    t1 = time.clock()
    print("dataset generated in ", (t1 - t0), "seconds.")
    pd.DataFrame(protein_drug_features.columns).to_csv(args.out_dir+"/"+output_file_name+"_features_list.csv")
    print("Total running time ", str(time.clock() - start_time), " seconds.")


def load_features(file_path, data_index):
    data = pd.read_csv(file_path, keep_default_na=False, dtype='object').set_index(data_index)
    return data

read_input_files()
