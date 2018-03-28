import pandas as pd
import numpy as np
import re

def read_csv_files(data):
    data_files = [
        "ap_2010.csv",
        "class_size.csv",
        "demographics.csv",
        "graduation.csv",
        "hs_directory.csv",
        "sat_results.csv"
    ]

    for f in data_files:
        d = pd.read_csv("/var/www/dataquest/lessons/schools/{0}".format(f))
        data[f.replace(".csv", "")] = d

    return data


def read_text_files(data):
    all_survey = pd.read_csv("/var/www/dataquest/lessons/schools/survey_all.txt", delimiter="\t", encoding='windows-1252')
    d75_survey = pd.read_csv("/var/www/dataquest//lessons/schools/survey_d75.txt", delimiter="\t", encoding='windows-1252')
    survey = pd.concat([all_survey, d75_survey], axis=0)

    survey["DBN"] = survey["dbn"]

    survey_fields = [
        "DBN",
        "rr_s",
        "rr_t",
        "rr_p",
        "N_s",
        "N_t",
        "N_p",
        "saf_p_11",
        "com_p_11",
        "eng_p_11",
        "aca_p_11",
        "saf_t_11",
        "com_t_11",
        "eng_t_10",
        "aca_t_11",
        "saf_s_11",
        "com_s_11",
        "eng_s_11",
        "aca_s_11",
        "saf_tot_11",
        "com_tot_11",
        "eng_tot_11",
        "aca_tot_11",
    ]

    survey = survey.loc[:,survey_fields]
    data["survey"] = survey

    return data

def add_dbn_column(data):
    data["hs_directory"]["DBN"] = data["hs_directory"]["dbn"]

    def _pad_csd(num):
        string_representation = str(num)
        if len(string_representation) > 1:
            return string_representation
        else:
            return "0" + string_representation

    def pad_csd(num):
        return str(num).zfill(2)

    data["class_size"]["padded_csd"] = data["class_size"]["CSD"].apply(pad_csd)
    data["class_size"]["DBN"] = data["class_size"]["padded_csd"] + data["class_size"]["SCHOOL CODE"]

    return data

def net_sat_results_score(data):
    cols = ['SAT Math Avg. Score', 'SAT Critical Reading Avg. Score', 'SAT Writing Avg. Score']

    for c in cols:
        #import ipdb; ipdb.set_trace()
        data['sat_results'][c] = pd.to_numeric(data['sat_results'][c], errors='coerce')

    data['sat_results']['sat_score'] = data['sat_results'][cols[0]] + data['sat_results'][cols[1]] + data['sat_results'][cols[2]]

    return data

def set_lat_lon(data):
    #import ipdb; ipdb.set_trace()
    def find_lat(loc):
        coords = re.findall("\(.+\)", loc)
        lat = coords[0].split(",")[0].replace("(", "")
        return lat

    def find_lon(loc):
        coords = re.findall("\(.+\)", loc)
        lon = coords[0].split(",")[1].replace(")", "")
        return lon

    data["hs_directory"]["lat"] = data["hs_directory"]["Location 1"].apply(find_lat)
    data["hs_directory"]["lon"] = data["hs_directory"]["Location 1"].apply(find_lon)

    data["hs_directory"]["lat"] = pd.to_numeric(data["hs_directory"]["lat"], errors="coerce")
    data["hs_directory"]["lon"] = pd.to_numeric(data["hs_directory"]["lon"], errors="coerce")

    return data

def condense_class_size(data):
    class_size = data["class_size"]
    class_size = class_size[class_size["GRADE "] == "09-12"]
    class_size = class_size[class_size["PROGRAM TYPE"] == "GEN ED"]

    # groupby
    class_size = class_size.groupby("DBN").agg(np.mean)
    class_size.reset_index(inplace=True)

    data["class_size"] = class_size
    return data

def condense_demographics(data):
    data["demographics"] = data["demographics"][data["demographics"]["schoolyear"] == 20112012]
    return data

def condense_graduation(data):
    data["graduation"] = data["graduation"][data["graduation"]["Cohort"] == "2006"]
    data["graduation"] = data["graduation"][data["graduation"]["Demographic"] == "Total Cohort"]
    return data

def merge(data):
    """
    left join  - will keep all DBN values in the left DF and assign null to those that are missing on the right
    right join - will keep all DBN values in the right DF and assign null to those that are missing on the left
    inner join - will keep only DBN values in common in both DF's and discard the one's missing from either DF
    outer join - will keep all DBN values from both DF's and assign null to those that are missing in both DF's (no rows are discarded)
    """
    combined = data["sat_results"]
    combined = combined.merge(data["ap_2010"], on="DBN", how="left")
    combined = combined.merge(data["graduation"], on="DBN", how="left")

    to_merge = ["class_size", "demographics", "survey", "hs_directory"]
    for m in to_merge:
        combined = combined.merge(data[m], on="DBN", how="inner")

    print('Merge Shape: {}'.format(combined.shape))
    data['combined'] = combined
    return data

def fillna(data):
    combined = data["combined"]
    combined = combined.fillna(combined.mean())
    combined = combined.fillna(0)
    data['combined'] = combined
    return data

def add_school_district(data):

    def get_first_two_chars(dbn):
        return dbn[0:2]

    combined = data["combined"]
    combined["school_dist"] = combined["DBN"].apply(get_first_two_chars)
    data['combined'] = combined
    return data

def main():
    """
    from utils import nyc_high_school
    data = nyc_high_school.main()
    data['combined']['school_dist'].unique()
    """
    data = {}
    data = read_csv_files(data)
    data = read_text_files(data)
    data = add_dbn_column(data)
    data = net_sat_results_score(data)
    data = set_lat_lon(data)

    # condensing lesson
    data = condense_class_size(data)
    data = condense_demographics(data)
    data = condense_graduation(data)
    data = merge(data)
    data = fillna(data)
    data = add_school_district(data)

    return data

if __name__ == '__main__':
    main()


