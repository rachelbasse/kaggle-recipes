#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# imports
from collections import Counter, defaultdict, namedtuple

#extra
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer


# In[ ]:


percent = lambda x, y: round(100 * x / y)


# In[ ]:


Ing = namedtuple('Ing', ['heads', 'states', 'brands', 'langs', 'cuisine', 'rcpid'])

def load_clean_data():
    recipes = pd.read_csv('data/cleaned_data.csv', header=0, index_col=0, encoding='utf-8',
                          # convert named tuple literals to Ings
                          converters={'ingredients': lambda x: eval(x)})
    print('{:,} recipes'.format(recipes.shape[0]))
    return recipes


# In[ ]:


def get_metrics(recipes):
    columns = []
    recipe_count = []
    recipe_mean_length = []
    head_count = []
    unique_count = []
    rare_count = []
    for cuisine, group in recipes.groupby('cuisine'):
        columns.append(cuisine)
        recipe_count.append(group.shape[0])
        recipe_mean_length.append(round(group.ingredients.apply(len).mean()))
        head_list = [ing.heads[0] for ings in group.ingredients for ing in ings]
        head_count.append(len(head_list))
        head_counts = Counter(head_list)
        unique_count.append(len(head_counts))
        rare_head = 0
        for head, count in head_counts.items():
            if count < 4:
                rare_head += 1
        rare_count.append(rare_head)
    rare_pct = [percent(rare, total) for rare, total in zip(rare_count, unique_count)]
    index = ['recipe_count', 'recipe_length', 'unique_count', 'head_count', 'rare_count', 'rare_pct', 'cuisine']
    metrics = pd.DataFrame([recipe_count, recipe_mean_length, unique_count, head_count, rare_count, rare_pct, columns],
                           index=index, columns=columns, dtype=np.uint32)
    return metrics.transpose()


# In[ ]:


def make_counts(ings, attribute, categories, attribute_type='list'):
    atts = defaultdict(list)
    for ing in iter(ings):
        if attribute_type == 'list':
            for att in getattr(ing, attribute):
                atts[att].append(ing.cuisine)
        if attribute_type == 'string':
            att = ' '.join(getattr(ing, attribute))
            atts[att].append(ing.cuisine)
    att_counts = {}
    for att, cuisine_list in atts.items():
        att_counts[att] = Counter(cuisine_list)
    counts = pd.DataFrame.from_dict(att_counts, orient='index', columns=categories, dtype=np.float64)
    counts.fillna(0.0, inplace=True)
    return counts


# In[ ]:


def normalize_counts(counts, weights=None):
    if weights:
        counts = counts.apply(lambda col: col.map(lambda x: x / weights[col.name]), axis='index')
    count_min = counts.values.min()
    count_range = counts.values.max() - count_min
    counts = counts.applymap(lambda x: (x - count_min) / count_range)
    return counts


# In[ ]:


def save_output(output):
    output = output.drop(columns=['ingredients'])
    
    train = output.query('cuisine != "test"')
    test = output.query('cuisine == "test"')
    
    train.cuisine.to_csv('data/cuisine.csv', header=False, encoding='utf-8')
    
    train = train.drop(columns=['cuisine'])
    test = test.drop(columns=['cuisine'])
    
    train.to_csv('data/temp_train.csv', header=True, encoding='utf-8') 
    test.to_csv('data/temp_test.csv', header=True, encoding='utf-8')


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




