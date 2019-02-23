#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# imports

# standard
from collections import Counter, defaultdict
from itertools import product
from math import log

#extra
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# In[ ]:


new_features = {
    'east': ['japanese', 'korean', 'vietnamese', 'chinese', 'thai', 'filipino', 'indian'],
    'west': ['russian', 'british', 'irish', 'french', 'italian', 'greek', 'spanish', 'cajun_creole',
             'moroccan', 'southern_us', 'mexican', 'jamaican', 'brazilian'],
    'frenchlike': ['british', 'french', 'russian'],
    'italianlike': ['greek', 'italian', 'mexican', 'spanish'],
    'japaneselike': ['chinese', 'indian', 'japanese', 'korean'],
    'mexicanlike': ['indian', 'mexican', 'thai', 'vietnamese'],
    'southern_uslike': ['cajun_creole', 'jamaican', 'mexican', 'southern_us']
}


# In[ ]:


def load_clean_data():
    recipes = pd.read_csv('data/cleaned_data.csv', header=0, index_col=0, encoding='utf-8',
                          # convert list literals to lists
                          converters={'ingredients': lambda x: eval(x)})
    print('{:,} recipes'.format(recipes.shape[0]))
    return recipes


# In[ ]:


flatten = lambda lists: [item for lst in lists for item in lst]


# In[ ]:


def remove_states(ings):
    return ings.map(lambda lst: [ing for ing in flatten(lst) if '_state' not in ing])


# In[ ]:


def remove_dupes(ings):
    return ings.map(set).map(list)


# In[ ]:


def update_names(ings, renamed):
    return [renamed[feature] if feature in renamed else feature for feature in ings]


# In[ ]:


def make_counts(recipes):
    counts = {}
    for cuisine, group in recipes.groupby('cuisine'):
        all_ings = flatten(group.ingredients.to_list())
        counts[cuisine] = Counter(all_ings)
    counts = pd.DataFrame.from_dict(counts, orient='columns', dtype=np.float64)
    counts.fillna(0.0, inplace=True)
    counts.test = 0.0
    print('{} features'.format(counts.shape[0]))
    return counts


# In[ ]:


def scale_counts(counts, scales):
    counts = counts.apply(lambda col: col.map(lambda x: x / scales[col.name]), axis='index')
    return counts


# In[ ]:


def merge_arrows(arrows, update):
    arrows.update(update)
    for origin, target in arrows.items():
        if target in arrows:
            arrows[origin] = arrows[target]
    return arrows

def get_target_feature(feature, bad_features, catchall):
    parts = feature.split('-')
    if parts[-1] == catchall:
        target = parts[0]
    else:
        parts[-1] = catchall
        target = '-'.join(parts)
    if target in bad_features:
        target = get_target_feature(target, bad_features, catchall)
    return target

def merge_features(counts, features_to_merge, catchall):
    renamed_features = {}
    counts = counts.copy()
    if catchall in features_to_merge:
        features_to_merge = features_to_merge.copy()
        features_to_merge.remove(catchall)
    features_to_keep = set(counts.index) - set(features_to_merge)
    for feature in features_to_merge:
        target = get_target_feature(feature, features_to_merge, catchall)
        renamed_features[feature] = target
        if target in features_to_keep:
            counts.loc[target] += counts.loc[feature]
            continue
        counts.loc[target] = counts.loc[feature]
    counts = counts.drop(index=features_to_merge)
    print('{} merged, {} features left'.format(len(renamed_features), len(counts)))
    return (counts, renamed_features)


# In[ ]:


def merge_rare_features(counts, cutoff, catchall):
    totals = counts.max(axis='columns')
    rare_features = totals[totals <= cutoff].index.to_list()
    long_features = [feature for feature in rare_features if len(feature.split('-')) > 1]
    merged, renamed = merge_features(counts, long_features, catchall)
    
    totals = merged.max(axis='columns')
    rare_features = totals[totals <= cutoff].index.to_list()
    raretype_features = [feature for feature in rare_features if len(feature.split('-')) > 1]
    merged, renamed_update = merge_features(merged, raretype_features, catchall)
    renamed = merge_arrows(renamed, renamed_update)
    
    totals = merged.max(axis='columns')
    rare_features = totals[totals <= cutoff].index.to_list()
    merged, renamed_update = merge_features(merged, rare_features, catchall)
    renamed = merge_arrows(renamed, renamed_update)
    
    return (merged, renamed)


# In[ ]:


def get_proportions(counts):
    total = counts.sum(axis='columns')
    inverse_total = total.map(lambda x: 1 / x if x else 0)
    proportions = counts.T * inverse_total
    return proportions.T


# In[ ]:


def make_scores(recipe, points, group=True):
    scores = points.loc[recipe.ingredients]
    if group:
        groups = scores.groupby(lambda ing: ing.split('-')[0])
        return groups.mean().mean()
    return scores.mean()


# In[ ]:


def add_score_features(scores):
    to_add = []
    for name, cats in new_features.items():
        series = scores[cats].mean(axis='columns')
        series.name = name
        to_add.append(series)
    scores = pd.concat([scores] + to_add, axis='columns')
    return scores


# In[ ]:


def plot_cnf(cm, classes):
    plt.figure(figsize=(9,9))
    plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=80)
    plt.yticks(tick_marks, classes)
    thresh = cm.max() / 2.
    for i, j in product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, format(cm[i, j], 'd'),
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")
    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    plt.tight_layout()
    plt.grid(False)


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

