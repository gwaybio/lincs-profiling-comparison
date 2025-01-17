#!/usr/bin/env python
# coding: utf-8

# ### Calculating Null Distribution
# 
# - Null distribution - is generated by getting the median correlation score of randomly combined compounds that do not share/come from the same MOAs.
# 
# 
# ### The goal here:
# - is to compute the p-value for each MOA per dose by evaluating the probability of random combinations of compounds (from different MOAs) having greater median correlation score than compounds of the same MOA.
# 
# 
# 
# 
# - In our case, we generated 1000 median correlation scores from randomly combined compounds as the **null distribution** for each MOA_SIZE class ***i.e. for a moa_size class - we have 1000 medians scores from randomly combined compounds of different MOAs.***
# 
# 
# 
# 
# - Moa_size is the number of compounds in a specific MOA and moa_size class is a specific group of MOAs that have the same number of compounds ***e.g all MOAs with just 2 compounds in them are in the same moa_size class.***
# 
# 
# ### Note:
# 
# To generate the null distribution for all the four consensus data, you will have to execute this notebook four times, one for each.

# In[1]:


import os
import pathlib
import pandas as pd
import numpy as np
from collections import defaultdict
import matplotlib.pyplot as plt
get_ipython().run_line_magic('matplotlib', 'inline')
import seaborn as sns
from pycytominer import feature_select
from statistics import median
import random
sns.set_style("darkgrid")
from scipy import stats
import pickle
from io import BytesIO
from urllib.request import urlopen
from zipfile import ZipFile


# In[2]:


np.random.seed(42)


# #### - Load in the datasets required, 
# 
# - They were generated from the `cell_painting_moa_median_scores_calculation notebook`

# In[3]:


data_moa = pd.read_csv(os.path.join('moa_sizes_consensus_datasets', 'modz_consensus_data.csv'))
data_moa_vals = pd.read_csv(os.path.join('moa_sizes_consensus_datasets', 'modz_moa_median_scores.csv'))
data_moa_cpds = pd.read_csv(os.path.join('moa_sizes_consensus_datasets', 'cellpainting_moa_compounds.csv'))


# In[4]:


data_moa.shape


# In[5]:


data_moa_vals.shape


# In[6]:


data_moa_cpds.shape


# In[7]:


def conv_cols_to_list(df_moa_cpds):
    """This function convert string values in compound dataframe to lists"""
    
    moa_cpd_cols = [col for col in df_moa_cpds.columns.tolist() 
                 if (col.startswith("moa_cpds_"))]
    for col in moa_cpd_cols:
        df_moa_cpds[col] = df_moa_cpds[col].apply(lambda row: row.split(';'))
    return df_moa_cpds


# In[8]:


data_moa_cpds = conv_cols_to_list(data_moa_cpds)


# In[9]:


def get_cpd_agg(data_moa, dose_number):
    """
    This function aggregate values for a particular 
    dose by taking the mean value of distinct compounds in the dose
    """
    
    df_dose = data_moa[data_moa['Metadata_dose_recode'] == dose_number].copy()
    meta_cols = [col for col in df_dose.columns.tolist() 
                 if (col.startswith("Metadata_"))]
    df_dose.drop(meta_cols, axis = 1, inplace = True)
    df_compound_agg = df_dose.groupby(['pert_iname']).agg(['mean'])
    df_compound_agg.columns  = df_compound_agg.columns.droplevel(1)
    df_compound_agg.rename_axis(None, axis=0, inplace = True)
    
    return df_compound_agg


# In[10]:


def cpds_found_in_all_doses(data_moa):
    """This function return a list of compounds found in all doses (1 - 6)"""
    cpds_fd = []
    for num in range(1,7):
        df_cpd_agg = get_cpd_agg(data_moa, num)
        all_cpds = df_cpd_agg.index.tolist()
        cpds_fd.append(all_cpds)
    
    cpds_fd_in_all = [cpd for list_cpds in cpds_fd 
                      for cpd in list_cpds 
                      if all(cpd in list_of_cpds for list_of_cpds in cpds_fd)]
    cpds_fd_in_all = list(set(cpds_fd_in_all))
    
    return cpds_fd_in_all


# In[11]:


cpds_fd_in_all = cpds_found_in_all_doses(data_moa)


# In[12]:


len(cpds_fd_in_all)


# In[13]:


all_moa_list = data_moa['moa'].unique().tolist()


# In[14]:


len(all_moa_list)


# In[15]:


all_moa_dict = {moa: [cpd for cpd in data_moa['pert_iname'][data_moa['moa']== moa].unique().tolist() 
                      if cpd in cpds_fd_in_all]
                for moa in all_moa_list}
all_moa_dict = {kys:all_moa_dict[kys] for kys in all_moa_dict if all_moa_dict[kys]}


# In[16]:


len(all_moa_dict)


# In[17]:


def generate_moa_size_dict(df_moa_cpds):
    """
    Generates a dictionary with distinct moa_sizes 
    (moa_size == number of compounds that is present in each MOA) 
    as the keys and all compounds of MOAs with that particular size as the values
    """
    moa_size_dict = {}
    for size in df_moa_cpds['moa_size'].unique():
        size_df = df_moa_cpds[df_moa_cpds['moa_size'] == size].drop(['moa_size', 'moa'], axis = 1)
        size_df_values = size_df.values.tolist()
        size_df_vals = list(set([cpd for size_list in size_df_values for sizes in size_list for cpd in sizes]))
        moa_size_dict[size] = size_df_vals
    return moa_size_dict


# In[18]:


moa_sizes_dict = generate_moa_size_dict(data_moa_cpds)


# In[19]:


len(data_moa_cpds['moa_size'].unique())


# In[20]:


len(moa_sizes_dict)


# In[23]:


moa_sizes_dict


# In[21]:


def check_similar_cpds(cpds, moa_dict):
    """This function checks if two compounds are found in the same moa"""
    
    for x in range(len(cpds)):
        for y in range(x+1, len(cpds)):
            for kys in moa_dict:
                if all(i in moa_dict[kys] for i in [cpds[x], cpds[y]]):
                    return True
    return False


# In[22]:


def get_random_cpds(all_cpds, moa_size, moa_cpds, all_moa_cpds):
    """
    This function return a list of random cpds that are not of the same moas 
    or found in the current moa cpd's list
    """
    while (True):
        random_cpds = random.sample(all_cpds, moa_size)
        if not (any(cpds in moa_cpds for cpds in random_cpds) & (check_similar_cpds(random_cpds, all_moa_cpds))):
            break
    return random_cpds


# #### - You only need to generate the null distribution once (i.e. you can re-use the pickled null distribution for other consensus data), since the 1000 lists of randomly generated compounds combinations  for each MOA are found in all doses and all consensus datasets

# In[23]:


def get_null_distribution_cpds(moa_size_dict, cpds_list, all_moa_dict, rand_num = 1000):
    
    """
    This function returns the null distribution dictionary, with MOAs as the keys and 
    1000 lists of randomly selected compounds combinations as the values for each MOA
    """
    null_distribution_moa = {}
    for size in moa_size_dict:
        moa_cpds = moa_size_dict[size]
        moa_cpds_list = []
        for idx in range(rand_num):
            start_again = True
            while (start_again):
                rand_cpds = get_random_cpds(cpds_list, size, moa_cpds, all_moa_dict)
                if rand_cpds not in moa_cpds_list:
                    start_again = False
            moa_cpds_list.append(rand_cpds)
        null_distribution_moa[size] = moa_cpds_list
    
    return null_distribution_moa


# In[24]:


null_distribution_moa = get_null_distribution_cpds(moa_sizes_dict, cpds_fd_in_all, all_moa_dict)


# In[25]:


#save the null_distribution_moa to pickle, you only need to run the code once
with open(os.path.join('moa_sizes_consensus_datasets', 'null_distribution.pickle'), 'wb') as handle:
    pickle.dump(null_distribution_moa, handle, protocol=pickle.HIGHEST_PROTOCOL)


# In[26]:


##load the null_distribution_moa from pickle
with open(os.path.join('moa_sizes_consensus_datasets', 'null_distribution.pickle'), 'rb') as handle:
    null_distribution_moa = pickle.load(handle)


# In[27]:


print('moa_size', '\tnumber of generated lists of randomly combined compounds')
for keys in null_distribution_moa:
    print(keys, '\t\t', len(null_distribution_moa[keys]))


# In[28]:


def assert_null_distribution(null_distribution_moa):
    
    """
    This function assert that each of the list in the 1000 lists of 
    random compounds combination for each MOA are distinct with no duplicates
    """
    
    duplicates_moa = {}
    for keys in null_distribution_moa:
        null_dist = null_distribution_moa[keys]
        for cpds_moa in null_dist:
            cpds_duplicates = []
            new_list = list(filter(lambda cpds_list: cpds_list != cpds_moa, null_dist))
            if (len(new_list) != len(null_dist) - 1):
                cpds_duplicates.append(cpds_moa)
        if cpds_duplicates:
            duplicates_moa[keys] = cpds_duplicates
    return duplicates_moa


# In[29]:


duplicates_cpds_list = assert_null_distribution(null_distribution_moa)


# In[30]:


duplicates_cpds_list ##no duplicate found


# In[31]:


def calc_null_dist_median_scores(data_moa, dose_num, moa_cpds_list):
    """
    This function calculate the median of the correlation 
    values for each of the list in the 1000 lists of 
    random compounds combination for each MOA
    """
    df_cpd_agg = get_cpd_agg(data_moa, dose_num)
    median_corr_list = []
    for list_of_cpds in moa_cpds_list:
        df_cpds = df_cpd_agg.loc[list_of_cpds]
        cpds_corr = df_cpds.T.corr(method = 'spearman').values
        median_corr_val = median(list(cpds_corr[np.triu_indices(len(cpds_corr), k = 1)]))
        median_corr_list.append(median_corr_val)
    return median_corr_list


# **A P value can be computed nonparametrically by evaluating the probability of random compounds of different MOAs having greater median similarity value than compounds of the same MOAs.**

# In[32]:


def get_p_value(median_scores_list, df_moa_values, dose_name, moa_name):
    """
    This function calculate the p-value from the 
    null_distribution median scores for each MOA
    """
    actual_med = df_moa_values.loc[moa_name, dose_name]
    p_value = np.sum(median_scores_list >= actual_med) / len(median_scores_list)
    return p_value


# In[33]:


def get_null_dist_median_scores(null_distribution_moa, df_moa):
    """ 
    This function calculate the median correlation scores for all 
    1000 lists of randomly combined compounds for each moa_size class 
    across all doses (1-6)
    """
    null_distribution_medians = {}
    for key in null_distribution_moa:
        median_score_list = []
        for num in range(1,7):
            moa_size_median_scores = calc_null_dist_median_scores(df_moa, num, null_distribution_moa[key])
            median_score_list.append(moa_size_median_scores)
        null_distribution_medians[key] = median_score_list
    return null_distribution_medians


# In[34]:


null_distribution_medns = get_null_dist_median_scores(null_distribution_moa, data_moa)


# In[35]:


def transform_dataframe(rep, rep_name):
    """
    Transforms replicate correlation dataframe to have 3 columns: 
    dose, correlation_values and type of replicates
    """
    df_reps = pd.DataFrame.from_dict(rep, orient='index').T
    rep_melt = df_reps.melt(var_name="dose", value_name="correlation_values")
    rep_melt['type'] = rep_name
    return rep_melt


# In[36]:


threshold_df = []
for n_replicate in null_distribution_medns.keys():
    matched_null = pd.DataFrame(null_distribution_medns[n_replicate])
    for dose, dose_row in matched_null.iterrows():
        thresh = dose_row.quantile(0.95)
        dose_id = dose + 1
        threshold_df.append([n_replicate, dose_id, thresh])
        
threshold_df = pd.DataFrame(threshold_df, columns=["n_replicates", "dose", "95th_threshold"])
threshold_df


# In[37]:


def get_moa_p_vals(null_dist_median, df_moa_values):
    """
    This function returns a dict, with MOAs as the keys and the MOA's 
    p-values for each dose (1-6) as the values
    """
    null_p_vals = {}
    df_moa_values = df_moa_values.set_index('moa').rename_axis(None, axis=0)
    for key in null_dist_median:
        df_moa_size = df_moa_values[df_moa_values['moa_size'] == key]
        for moa in df_moa_size.index:
            dose_p_values = []
            for num in range(1,7):
                dose_name = 'dose_' + str(num)
                moa_p_value = get_p_value(null_dist_median[key][num-1], df_moa_size, dose_name, moa)
                dose_p_values.append(moa_p_value)
            null_p_vals[moa] = dose_p_values
    sorted_null_p_vals = {key:value for key, value in sorted(null_p_vals.items(), key=lambda item: item[0])}
    return sorted_null_p_vals


# In[38]:


null_p_vals = get_moa_p_vals(null_distribution_medns, data_moa_vals)


# In[39]:


df_null_p_vals = pd.DataFrame.from_dict(null_p_vals, orient='index', 
                                        columns = ['dose_' + str(x) 
                                                   for x in range(1,7)]).reset_index().rename(columns={"index": "moa"})


# In[40]:


df_null_p_vals['moa_size'] = data_moa_vals['moa_size']


# In[41]:


df_null_p_vals.shape


# In[42]:


df_null_p_vals.head(10)


# In[43]:


def save_to_csv(df, path, file_name):
    """saves moa dataframes to csv"""
    
    if not os.path.exists(path):
        os.mkdir(path)
    
    df.to_csv(os.path.join(path, file_name), index=False)


# In[44]:


save_to_csv(df_null_p_vals, 'moa_sizes_consensus_datasets', 'modz_null_p_values.csv')


# In[45]:


# Output files for visualization
cpd_summary_file = pathlib.Path("moa_sizes_consensus_datasets/matching_score_per_MOA_CellPainting_p_values_compared_to_nonparametric_null.tsv.gz")

dose_recode_info = {
    'dose_1': '0.04 uM', 'dose_2':'0.12 uM', 'dose_3':'0.37 uM',
    'dose_4': '1.11 uM', 'dose_5':'3.33 uM', 'dose_6':'10 uM'
}

cpd_score_summary_df = (
    df_null_p_vals
    .rename(columns={"moa_size": "no_of_replicates"})
    .melt(
        id_vars=["moa", "no_of_replicates"],
        value_vars=["dose_1", "dose_2", "dose_3", "dose_4", "dose_5", "dose_6"],
        var_name="dose",
        value_name="p_value"
    )
)

cpd_score_summary_df.dose = cpd_score_summary_df.dose.replace(dose_recode_info)

cpd_score_summary_df.to_csv(cpd_summary_file, sep="\t", index=False)
cpd_score_summary_df.head()

