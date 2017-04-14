import argparse

import pandas as pd

parser = argparse.ArgumentParser(description="Process files containing protein binding affinity features")

parser.add_argument('--p', type=str, nargs='+', help="list paths of files containing protein features")

parser.add_argument('--f', type=str, help="list paths of files containing protein-molecular compound features")

parser.add_argument('--m', type=str, help="file containing molecular descriptors")

parser.add_argument('--feats', type=str, help="file containing which molecular descriptors to keep")
args = parser.parse_args()


def read_input_files():
    # create an empty list to store the dataframes of protein features
    df_pro_list = []

    # for each input file of protein features, load the dataframe then append to the dataframe list
    for path in args.p:
        df = parse_file(path)
        df_pro_list.append(df)

    # do a pairwise merge (inner join) for each dataframe in the dataframe list
    df_agg_pro = reduce(lambda x, y: pd.merge(x, y, on=["proteinName"]), df_pro_list)

    print df_agg_pro.shape

    # read protein-molecular features file
    pro_drug_df = parse_file(args.f)

    print pro_drug_df.shape

    # merge protein-molecular features with protein features
    pro_drug_all_df = pd.merge(pro_drug_df, df_agg_pro, how='left', on='proteinName')

    print pro_drug_all_df.shape

    # read molecular features file
    mol_df = parse_file(args.m)

    print mol_df.shape

    # do a pairwise merge (inner join) of molecular features with all protein-molecular features
    output_df = pd.merge(pro_drug_all_df, mol_df, on="moleculeName")

    print output_df.shape

    # output the aggregated dataframe to .csv
    # TODO: fix the formatting of the output file to have the keys justified to the left and data following on the right

    output_df.to_csv('ml_pro_features.csv', index=False)


def parse_file(filepath):
    '''
        Given a filepath, determines which parser to run in order to extract data. Returns a pandas DataFrame.
        :param filepath: path to the input file
        :return: pandas DataFrame
        '''

    data = pd.DataFrame()

    if filepath.find('docking') != -1:
        data = load_protein_molecular_features(filepath)
    elif filepath.find('MolecularDescriptors') != -1:
        data = load_molecular_descriptors(filepath, args.feats)
    elif filepath.find('protein_features') != -1:  # protein_features_coach_avg and protein_features_2struc
        data = load_protein_features(filepath)
    else:
        print 'File not supported'

    return data


# create a function for reading each input file type

def load_molecular_descriptors(filepath, descriptorsListFile=None):
    '''
        reads input files containing molecular descriptors
        :param filepath: path to the input file
        :return: pandas DataFrame
        '''

    data = pd.read_csv(filepath, delimiter='\t', low_memory=False)

    # rename duplicated moleculars
    for index, row in data.iterrows():
        molName = data.get_value(index, 'NAME', takeable=False)
        if (molName.find('_') == -1):
            duplicatedMol = data.loc[data['NAME'] == molName]
            rowNum = len(duplicatedMol.index)

            # there are duplicated Mol.
            # rename from second molecule _#
            molIndex = 0
            if (rowNum > 1):
                for innerIndex, innerRow in duplicatedMol.iterrows():
                    molIndex = molIndex + 1
                    if (molIndex > 1):
                        newMolName = molName + '_' + str(molIndex)
                        data.set_value(innerIndex, 'NAME', newMolName)

    # select descriptorsList if there is
    if (descriptorsListFile != None):
        with open(descriptorsListFile) as f:
            descriptorsList = f.read().splitlines()

        descriptorsList.append('NAME')

        # Doesn't work becuase may some columns are not exist in the data when we use outputExclusionMolecularDescriptors.txt
        # data = data[descriptorsList]

        for index, column in data.iteritems():  # index =  column name
            if (index not in descriptorsList):
                data.drop(index, axis=1, inplace=True)

    # rename the second column to use it as key in the merge
    data.rename(columns={'NAME': 'moleculeName'}, inplace=True)

    return data


def load_protein_molecular_features(filepath):
    data = pd.read_csv(filepath)

    # extract protein name from Ligand and store it in new column
    data['proteinName'] = data['Filename'].str.extract('(...._cluster\d+)', expand=True)

    # extract molecule name from Ligand and store it in new column
    data['moleculeName'] = data['Filename'].str.extract('((?<=cluster\d_)\w+)', expand=True)

    # colunms' name to keep
    columns = ['proteinName', 'moleculeName', 'dockingEnergy', 'mmgbsaEnergy', 'avg_gauss1', 'avg_gauss2',
               'avg_repulsion', 'avg_hydrophobic', 'avg_hydrogen', 'Model1.gauss1', 'Model1.gauss2', 'Model1.repulsion',
               'Model1.hydrophobic', 'Model1.hydrogen', 'label']

    data = data[columns]

    return data


def load_protein_features(filepath):
    '''
        reads protein_features_2struc
        :param filepath: path to the input file
        :return: pandas DataFrame
        '''
    data = pd.read_csv(filepath, delimiter=',')

    # rename the first column to use it as key in the merge

    if ((list(data.columns.values))[0] == 'Cluster_Name'):  # protein_features_2struc.csv
        data.rename(columns={'Cluster_Name': 'proteinName'}, inplace=True)
    elif ((list(data.columns.values))[0] == 'cluster_name'):  # protein_features_coach_avg.csv
        data.rename(columns={'cluster_name': 'proteinName'}, inplace=True)
    return data


read_input_files()
