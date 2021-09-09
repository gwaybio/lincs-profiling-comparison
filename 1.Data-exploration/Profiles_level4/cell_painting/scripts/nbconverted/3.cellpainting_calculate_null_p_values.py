#!/usr/bin/env python
# coding: utf-8

# ### Calculating Null Distribution
# 
# 
# 
# Null distribution - is generated by getting the median correlation score of randomly combined replicates that do not come from the same compounds.
# 
# 
# 
# ### The goal here: 
# 
# -- is to compute the **p-value** for each compound per dose by evaluating the probability of random combinations of replicates (from different compounds) having greater median correlation score than replicates that come from the same compound.
# 
# 
# 
# 
# - In our case, we generated 1000 median correlation scores from randomly combined replicates as the **null distribution** for each no_of_replicates/replicate class per DOSE i.e. for a no_of_replicates class for every DOSE (1-6) - we have 1000 medians scores from randomly combined replicates of different compounds.
# 
# 
# 
# 
# 
# **no_of_replicate** is the number of replicates in a specific compound and **no_of_replicate class** is a specific group of compounds that have the same amount of replicates e.g all compounds with 5 replicates in them are in the same no_of_replicates class.

# In[1]:


import os
import pathlib
import pandas as pd
import numpy as np
from collections import defaultdict
from pycytominer import feature_select
from statistics import median
import random
from scipy import stats
import pickle


import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
np.warnings.filterwarnings('ignore', category=np.VisibleDeprecationWarning)


# In[2]:


np.random.seed(42)


# In[3]:


# Load common compounds
common_file = pathlib.Path(
    "..", "..", "..", "6.paper_figures", "data", "significant_compounds_by_threshold_both_assays.tsv.gz"
)
common_df = pd.read_csv(common_file, sep="\t")

common_compounds = common_df.compound.unique()
print(len(common_compounds))


# ### - Load in Level 4 Datasets generated from `calculate_median_scores_notebook`

# In[4]:


cp_level4_path = "cellpainting_lvl4_cpd_replicate_datasets"


# In[5]:


df_level4 = pd.read_csv(os.path.join(cp_level4_path, 'cp_level4_cpd_replicates.csv.gz'), 
                        compression='gzip',low_memory = False)

print(df_level4.shape)
df_level4.head()


# In[6]:


df_cpd_med_scores = pd.read_csv(os.path.join(cp_level4_path, 'cpd_replicate_median_scores.csv'))
df_cpd_med_scores = df_cpd_med_scores.set_index('cpd').rename_axis(None, axis=0).copy()

# Subset to common compound measurements
df_cpd_med_scores = df_cpd_med_scores.loc[df_cpd_med_scores.index.isin(common_compounds), :]

print(df_cpd_med_scores.shape)
df_cpd_med_scores.head()


# In[7]:


def get_cpds_replicates(df, df_lvl4):
    """
    This function returns all replicates id/names found in each compound 
    and in all doses(1-6)
    """
    
    dose_list = list(set(df_lvl4['Metadata_dose_recode'].unique().tolist()))[1:7]
    replicates_in_all = []
    cpds_replicates = {}
    for dose in dose_list:
        rep_list = []
        df_doses = df_lvl4[df_lvl4['Metadata_dose_recode'] == dose].copy()
        for cpd in df.index:
            replicate_names = df_doses[df_doses['pert_iname'] == cpd]['replicate_name'].values.tolist()
            rep_list += replicate_names
            if cpd not in cpds_replicates:
                cpds_replicates[cpd] = [replicate_names]
            else:
                cpds_replicates[cpd] += [replicate_names]
        replicates_in_all.append(rep_list)
        
    return replicates_in_all, cpds_replicates


# In[8]:


replicates_in_all, cpds_replicates = get_cpds_replicates(df_cpd_med_scores, df_level4)


# In[9]:


def get_replicates_classes_per_dose(df, df_lvl4, cpds_replicates):
    
    """
    This function gets all replicates ids for each distinct 
    no_of_replicates (i.e. number of replicates per cpd) class per dose (1-6)
    
    Returns replicate_class_dict dictionary, with no_of_replicate classes as the keys, 
    and all the replicate_ids for each no_of_replicate class as the values
    """
    
    df['replicate_id'] = list(cpds_replicates.values())
    dose_list = list(set(df_lvl4['Metadata_dose_recode'].unique().tolist()))[1:7]
    replicate_class_dict = {}
    for dose in dose_list:
        for size in df['no_of_replicates'].unique():
            rep_lists = []
            for idx in range(df[df['no_of_replicates'] == size].shape[0]):
                rep_ids = df[df['no_of_replicates'] == size]['replicate_id'].values.tolist()[idx][dose-1]
                rep_lists += rep_ids
            if size not in replicate_class_dict:
                replicate_class_dict[size] = [rep_lists]
            else:
                replicate_class_dict[size] += [rep_lists]
                
    return replicate_class_dict


# In[10]:


cpd_replicate_class_dict = get_replicates_classes_per_dose(df_cpd_med_scores, df_level4, cpds_replicates)


# In[11]:


cpd_replicate_class_dict.keys()


# In[12]:


def check_similar_replicates(replicates, dose, cpd_dict):
    """This function checks if two replicates are of the same compounds"""
    
    for x in range(len(replicates)):
        for y in range(x+1, len(replicates)):
            for kys in cpd_dict:
                if all(i in cpd_dict[kys][dose-1] for i in [replicates[x], replicates[y]]):
                    return True
    return False


# In[13]:


def get_random_replicates(all_replicates, no_of_replicates, dose, replicates_ids, cpd_replicate_dict):
    """
    This function return a list of random replicates that are not of the same compounds
    or found in the current cpd's size list
    """
    while (True):
        random_replicates = random.sample(all_replicates, no_of_replicates)
        if not (any(rep in replicates_ids for rep in random_replicates) & 
                (check_similar_replicates(random_replicates, dose, cpd_replicate_dict))):
            break
    return random_replicates


# In[14]:


def get_null_distribution_replicates(
    cpd_replicate_class_dict,
    dose_list,
    replicates_lists,
    cpd_replicate_dict,
    rand_num = 1000
):
    
    """
    This function returns a null distribution dictionary, with no_of_replicates(replicate class) 
    as the keys and 1000 lists of randomly selected replicate combinations as the values
    for each no_of_replicates class per DOSE(1-6)
    """
    random.seed(1903)
    null_distribution_reps = {}
    for dose in dose_list:
        for replicate_class in cpd_replicate_class_dict:
            replicates_ids = cpd_replicate_class_dict[replicate_class][dose-1]
            replicate_list = []
            for idx in range(rand_num):
                start_again = True
                while (start_again):
                    rand_cpds = get_random_replicates(replicates_lists[dose-1], replicate_class, dose, 
                                                      replicates_ids, cpd_replicate_dict)
                    if rand_cpds not in replicate_list:
                        start_again = False
                replicate_list.append(rand_cpds)
            if replicate_class not in null_distribution_reps:
                null_distribution_reps[replicate_class] = [replicate_list]
            else:
                null_distribution_reps[replicate_class] += [replicate_list]
    
    return null_distribution_reps


# In[15]:


len(cpds_replicates.keys())


# In[16]:


dose_list = list(set(df_level4['Metadata_dose_recode'].unique().tolist()))[1:7]

null_distribution_replicates = get_null_distribution_replicates(
    cpd_replicate_class_dict, dose_list, replicates_in_all, cpds_replicates
)


# In[17]:


def save_to_pickle(null_distribution, path, file_name):
    """This function saves the null distribution replicates ids into a pickle file"""
    
    if not os.path.exists(path):
        os.mkdir(path)
        
    with open(os.path.join(path, file_name), 'wb') as handle:
        pickle.dump(null_distribution, handle, protocol=pickle.HIGHEST_PROTOCOL)


# In[18]:


#save the null_distribution_moa to pickle
save_to_pickle(null_distribution_replicates, cp_level4_path, 'null_distribution.pickle')


# In[19]:


##load the null_distribution_moa from pickle
with open(os.path.join(cp_level4_path, 'null_distribution.pickle'), 'rb') as handle:
    null_distribution_replicates = pickle.load(handle)


# In[20]:


def assert_null_distribution(null_distribution_reps, dose_list):
    
    """
    This function assert that each of the list in the 1000 lists of random replicate 
    combination (per dose) for each no_of_replicate class are distinct with no duplicates
    """
    duplicates_reps = {}
    for dose in dose_list:
        for keys in null_distribution_reps:
            null_dist = null_distribution_reps[keys][dose-1]
            for reps in null_dist:
                dup_reps = []
                new_list = list(filter(lambda x: x != reps, null_dist))
                if (len(new_list) != len(null_dist) - 1):
                    dup_reps.append(reps)
            if dup_reps:
                if keys not in duplicates_reps:
                    duplicates_reps[keys] = [dup_reps]
                else:
                    duplicates_reps[keys] += [dup_reps]
    return duplicates_reps


# In[21]:


duplicate_replicates = assert_null_distribution(null_distribution_replicates, dose_list)


# In[22]:


duplicate_replicates ##no duplicates


# In[23]:


def calc_null_dist_median_scores(df, dose_num, replicate_lists):
    """
    This function calculate the median of the correlation 
    values for each list in the 1000 lists of random replicate 
    combination for each no_of_replicate class per dose
    """
    df_dose = df[df['Metadata_dose_recode'] == dose_num].copy()
    df_dose = df_dose.set_index('replicate_name').rename_axis(None, axis=0)
    df_dose.drop(['Metadata_broad_sample', 'Metadata_pert_id', 'Metadata_dose_recode', 
                  'Metadata_Plate', 'Metadata_Well', 'Metadata_broad_id', 'Metadata_moa', 
                  'broad_id', 'pert_iname', 'moa'], 
                 axis = 1, inplace = True)
    median_corr_list = []
    for rep_list in replicate_lists:
        df_reps = df_dose.loc[rep_list].copy()
        reps_corr = df_reps.astype('float64').T.corr(method = 'spearman').values
        median_corr_val = median(list(reps_corr[np.triu_indices(len(reps_corr), k = 1)]))
        median_corr_list.append(median_corr_val)
    return median_corr_list


# In[24]:


def get_null_dist_median_scores(null_distribution_cpds, dose_list, df):
    """ 
    This function calculate the median correlation scores for all 
    1000 lists of randomly combined compounds for each no_of_replicate class 
    across all doses (1-6)
    """
    null_distribution_medians = {}
    for key in null_distribution_cpds:
        median_score_list = []
        for dose in dose_list:
            replicate_median_scores = calc_null_dist_median_scores(df, dose, null_distribution_cpds[key][dose-1])
            median_score_list.append(replicate_median_scores)
        null_distribution_medians[key] = median_score_list
    return null_distribution_medians


# In[25]:


null_distribution_medians = get_null_dist_median_scores(null_distribution_replicates, dose_list, df_level4)


# In[26]:


def compute_dose_median_scores(null_dist_medians, dose_list):
    """
    This function align median scores per dose, and return a dictionary, 
    with keys as dose numbers and values as all median null distribution/non-replicate correlation 
    scores for each dose
    """
    median_scores_per_dose = {}
    for dose in dose_list:
        median_list = []
        for keys in null_distribution_medians:
            dose_median_list = null_distribution_medians[keys][dose-1]
            median_list += dose_median_list
        median_scores_per_dose[dose] = median_list
    return median_scores_per_dose


# In[27]:


dose_null_medians = compute_dose_median_scores(null_distribution_medians, dose_list)


# In[28]:


#save the null_distribution_medians_per_dose to pickle
save_to_pickle(dose_null_medians, cp_level4_path, 'null_dist_medians_per_dose.pickle')


# **A P value can be computed nonparametrically by evaluating the probability of random replicates of different compounds having median similarity value greater than replicates of the same compounds.**

# In[29]:


def get_p_value(median_scores_list, df, dose_name, cpd_name):
    """
    This function calculate the p-value from the 
    null_distribution median scores for each compound
    """
    actual_med = df.loc[cpd_name, dose_name]
    p_value = np.sum(median_scores_list >= actual_med) / len(median_scores_list)
    return p_value


# In[30]:


def get_moa_p_vals(null_dist_median, dose_list, df_med_values):
    """
    This function returns a dict, with compounds as the keys and the compound's 
    p-values for each dose (1-6) as the values
    """
    null_p_vals = {}
    for key in null_dist_median:
        df_replicate_class = df_med_values[df_med_values['no_of_replicates'] == key]
        for cpd in df_replicate_class.index:
            dose_p_values = []
            for num in dose_list:
                dose_name = 'dose_' + str(num)
                cpd_p_value = get_p_value(null_dist_median[key][num-1], df_replicate_class, dose_name, cpd)
                dose_p_values.append(cpd_p_value)
            null_p_vals[cpd] = dose_p_values
    sorted_null_p_vals = {key:value for key, value in sorted(null_p_vals.items(), key=lambda item: item[0])}
    return sorted_null_p_vals


# In[31]:


null_p_vals = get_moa_p_vals(null_distribution_medians, dose_list, df_cpd_med_scores)


# In[32]:


df_null_p_vals = pd.DataFrame.from_dict(null_p_vals, orient='index', columns = ['dose_' + str(x) for x in dose_list])


# In[33]:


df_null_p_vals['no_of_replicates'] = df_cpd_med_scores['no_of_replicates']


# In[34]:


df_null_p_vals.head(10)


# In[35]:


def save_to_csv(df, path, file_name):
    """saves dataframes to csv"""
    
    if not os.path.exists(path):
        os.mkdir(path)
    
    df.to_csv(os.path.join(path, file_name), index = False)


# In[36]:


save_to_csv(df_null_p_vals.reset_index().rename({'index':'cpd'}, axis = 1), cp_level4_path, 
            'cpd_replicate_p_values.csv')


# In[37]:


cpd_summary_file = pathlib.Path(cp_level4_path, 'cpd_replicate_p_values_melted.csv')

dose_recode_info = {
    'dose_1': '0.04 uM', 'dose_2':'0.12 uM', 'dose_3':'0.37 uM',
    'dose_4': '1.11 uM', 'dose_5':'3.33 uM', 'dose_6':'10 uM'
}

# Melt the p values
cpd_score_summary_pval_df = (
    df_null_p_vals
    .reset_index()
    .rename(columns={"index": "compound"})
    .melt(
        id_vars=["compound", "no_of_replicates"],
        value_vars=["dose_1", "dose_2", "dose_3", "dose_4", "dose_5", "dose_6"],
        var_name="dose",
        value_name="p_value"
    )
)

cpd_score_summary_pval_df.dose = cpd_score_summary_pval_df.dose.replace(dose_recode_info)

# Melt the median matching scores
cpd_score_summary_df = (
    df_cpd_med_scores
    .reset_index()
    .rename(columns={"index": "compound"})
    .melt(
        id_vars=["compound", "no_of_replicates"],
        value_vars=["dose_1", "dose_2", "dose_3", "dose_4", "dose_5", "dose_6"],
        var_name="dose",
        value_name="matching_score"
    )

)

cpd_score_summary_df.dose = cpd_score_summary_df.dose.replace(dose_recode_info)

summary_df = (
    cpd_score_summary_pval_df
    .merge(cpd_score_summary_df, on=["compound", "no_of_replicates", "dose"], how="inner")
    .assign(
        assay="Cell Painting",
        normalization="spherized",
        category="all_data"
    )
)

summary_df.to_csv(cpd_summary_file, sep="\t", index=False)

print(summary_df.shape)
summary_df.head()

