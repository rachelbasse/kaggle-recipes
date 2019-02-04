#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# imports
from collections import Counter

#extra
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer


# In[ ]:


def load_clean_data():
    recipes = pd.read_csv('data/cleaned_data.csv', header=0, index_col=0, encoding='utf-8',
                          # convert list literals to lists
                          converters={'ingredients': lambda x: x[2:-2].split("', '")})
    print('{:,} recipes'.format(recipes.shape[0]))
    return recipes


# In[ ]:


def get_metrics(recipes):
    columns = []
    recipe_count = []
    recipe_mean_length = []
    ing_count = []
    unique_count = []
    rare_count = []
    for cuisine, group in recipes.groupby('cuisine'):
        columns.append(cuisine)
        recipe_count.append(group.shape[0])
        recipe_mean_length.append(round(group.ingredients.apply(len).mean()))
        ing_list = [ing for ings in group.ingredients for ing in ings]
        ing_count.append(len(ing_list))
        ing_counts = Counter(ing_list)
        unique_count.append(len(ing_counts))
        rare_count.append(sum((1 if count == 1 else 0 for count in ing_counts.values())))
    rare_pct = [round(100 * rare / total) for rare, total in zip(rare_count, ing_count)]
    index = ['recipe_count', 'recipe_length', 'unique_count', 'ing_count', 'rare_count', 'rare_pct', 'cuisine']
    metrics = pd.DataFrame([recipe_count, recipe_mean_length, unique_count, ing_count, rare_count, rare_pct, columns],
                           index=index, columns=columns, dtype=np.uint32)
    return metrics.transpose()


# In[ ]:


def make_tfidfs(recipes):
    doc_names = []
    doc_strings = []
    for cuisine, group in recipes.groupby('cuisine'):
        doc_names.append(cuisine)
        doc_strings.append(' '.join([ing for ings in group.ingredients for ing in ings]))
    vectorizer = TfidfVectorizer(encoding='utf-8', ngram_range=(1, 1), max_df=1.0, min_df=1, max_features=None, 
                                 strip_accents=None, token_pattern=r'[\w-]+', analyzer='word', stop_words=None)
    tfidfs = vectorizer.fit_transform(doc_strings)
    feature_names = vectorizer.get_feature_names()
    tfidfs = pd.SparseDataFrame(tfidfs).to_dense()
    tfidfs.fillna(0, inplace=True)
    tfidfs.index = doc_names
    tfidfs.columns = feature_names
    return tfidfs


# In[ ]:


def smooth_tfidfs(tfidfs, intensity):
    tfidf_fracs = tfidfs / tfidfs.sum(axis='index')
    smooth_tails = lambda x: x / (intensity + x)
    return tfidf_fracs.applymap(smooth_tails)


# In[ ]:




