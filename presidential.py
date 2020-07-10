import os
from string import ascii_uppercase
import re
import pandas as pd

class Presidential:
    def __init__(self, folder_name):
        self._folder_name = folder_name
    def get_file_county_names(self):
        files = [i for i in os.listdir(self._folder_name) if not i.startswith('.')] # to skip those hidden files
        county_list = [re.split("\(|\)", f)[1] for f in files]
        return files, county_list
    def tidy_dataframe(self, df):
        # updating columns attributes 
        n_cols = df.columns.size
        n_candidates = n_cols - 11
        id_vars = ['town', 'village', 'office']
        candidates = list(df.columns[3:(3 + n_candidates)])
        office_cols = list(ascii_uppercase[:8])
        col_names = id_vars + candidates + office_cols
        df.columns = col_names
        # forward-fill town values
        filled_town = df['town'].fillna(method='ffill')
        df = df.assign(town=filled_town)
        # removing summations
        df = df.dropna()
        # removing extra spaces
        stripped_town = df['town'].str.replace("\u3000", "")
        df = df.assign(town=stripped_town)
        # pivoting
        df = df.drop(labels=office_cols, axis=1)
        tidy_df = pd.melt(df,
                          id_vars=id_vars,
                          var_name='candidate_info',
                          value_name='votes'
                         )
        return tidy_df
    def get_presidential(self):
        presidential = pd.DataFrame()
        files, county_list = self.get_file_county_names()
        for file, county in zip(files, county_list):
            spreadsheet_path = "{}/{}".format(self._folder_name, file)
            # skip those combined cells
            df = pd.read_excel(spreadsheet_path, skiprows=[0, 1, 3, 4], thousands=',')
            tidy_df = self.tidy_dataframe(df)
            # appending dataframe of each city/county
            tidy_df['county'] = county
            presidential = presidential.append(tidy_df)
            print("Tidying {}".format(file))
        presidential = presidential.reset_index(drop=True) # reset index for the appended dataframe
        return presidential
    def adjust_presidential_df(self):
        presidential = self.get_presidential()
        # split candidate information into 2 columns
        candidate_info_df = presidential['candidate_info'].str.split("\n", expand=True)
        numbers = candidate_info_df[0].str.replace("\(|\)", "")
        candidates = candidate_info_df[1].str.cat(candidate_info_df[2], sep="/")
        # re-arrange columns
        presidential = presidential.drop(labels='candidate_info', axis=1)
        presidential['number'] = numbers
        presidential['candidate'] = candidates
        presidential['office'] = presidential['office'].astype(int)
        presidential = presidential[['county', 'town', 'village', 'office', 'number', 'candidate', 'votes']]
        return presidential