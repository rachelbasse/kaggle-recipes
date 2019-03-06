#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# imports

# standard
from collections import Counter, defaultdict
from itertools import combinations, product
from math import log

#extra
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# In[ ]:


def load_clean_data():
    recipes = pd.read_csv('data/cleaned_data.csv', header=0, index_col=0, encoding='utf-8',
                          # convert list literals to lists
                          converters={'ingredients': lambda x: eval(x), 'strings': lambda x: eval(x)})
    print('{:,} recipes'.format(recipes.shape[0]))
    return recipes


# In[ ]:


flatten = lambda lists: [item for lst in lists for item in lst]
inverse = lambda x: 1 / x if x else 0
rank = lambda score: score * inverse(score.max())
ratio = lambda score: score * inverse(score.mean())


# In[ ]:


def remove_dupes(ings):
    return ings.map(set).map(list)


# In[ ]:


def add_combos(ings):
    combos = lambda lst: lst + list(map('+'.join, combinations(sorted(lst), 2)))
    return ings.map(combos)


# In[ ]:


def update_names(ings, renamed):
    return [renamed[feature] if feature in renamed else feature for feature in ings]


# In[ ]:


def make_counts(recipes, field='ingredients'):
    counts = {}
    for cuisine, group in recipes.groupby('cuisine'):
        all_ings = flatten(group[field].to_list())
        counts[cuisine] = Counter(all_ings)
    counts = pd.DataFrame.from_dict(counts, orient='columns', dtype=np.float64)
    counts.fillna(0.0, inplace=True)
    counts.test = 0.0
    print('{} features'.format(counts.shape[0]))
    return counts


# In[ ]:


def min_max_scale(series):
    series_min = series.min()
    scaled = series - series_min
    series_max = scaled.max()
    return series / series_max


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


def merge_rare_features(counts, single_cutoff, combo_cutoff, catchall):
    totals = counts.max(axis='columns')
    rare_combo_features = totals[totals <= combo_cutoff].index.to_list()
    combo_features = [feature for feature in rare_combo_features if '+' in feature]
    merged = counts.drop(index=combo_features)
    print('{} combo features dropped'.format(len(combo_features)))
    renamed = {old: 'rarecombotype' for old in combo_features}

    totals = merged.max(axis='columns')
    rare_features = totals[totals <= single_cutoff].index.to_list()
    long_features = [feature for feature in rare_features if len(feature.split('-')) > 1]
    merged, renamed_update = merge_features(merged, long_features, catchall)
    renamed = merge_arrows(renamed, renamed_update)
    
    totals = merged.max(axis='columns')
    rare_features = totals[totals <= single_cutoff].index.to_list()
    raretype_features = [feature for feature in rare_features if len(feature.split('-')) > 1]
    merged, renamed_update = merge_features(merged, raretype_features, catchall)
    renamed = merge_arrows(renamed, renamed_update)
    
    totals = merged.max(axis='columns')
    rare_features = totals[totals <= single_cutoff].index.to_list()
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


def make_indicators(recipes, features):
    indicators = np.zeros([recipes.shape[0], len(features)], dtype=np.uint8)
    feature_index = {feature: i for i, feature in enumerate(features)}
    for row_i, ings in enumerate(recipes.ingredients):
        for feature in ings:
            indicators[row_i, feature_index[feature]] = 1
    indicators = pd.DataFrame(indicators, index=recipes.index, columns=features)
    return indicators


# In[ ]:


def reweight(data, weights):
    smooth = lambda data, w: data.map(lambda x: w[0] * log(1.01 + (x / (w[1] + x))) if x else 0)
    adjusted = data.copy()
    for col, weight in weights.items():
        adjusted[col] = smooth(adjusted[col], weight)
    return adjusted


# In[ ]:


def make_scores(recipe, points):
    scores = points.loc[recipe.ingredients]
    sums = scores.sum(axis='columns')
    mean_sum = sums.mean()
    groups = scores.groupby(lambda name: sums[name] > mean_sum, axis='index', sort=False).mean()
    low = groups.loc[False].add_prefix('low_')
    return pd.concat([scores.mean(), low], axis='index')


# In[ ]:


def ings_only(data):
    adjusted = data.copy()
    to_zero = [feature for feature in adjusted.index if '_brand' in feature or '_lang' in feature]
    adjusted.loc[to_zero] = 0
    return adjusted


# In[ ]:


groups = {
    'east': ['chinese', 'filipino', 'indian', 'japanese', 'korean', 'thai', 'vietnamese'],
    'west': ['russian', 'british', 'irish', 'french', 'italian', 'greek', 'spanish', 'cajun_creole',
             'moroccan', 'southern_us', 'mexican', 'jamaican', 'brazilian'],
    'chineselike': ['chinese', 'filipino', 'japanese', 'korean', 'thai', 'vietnamese'],
    'indianlike': ['indian', 'japanese', 'mexican', 'moroccan', 'southern_us', 'thai'],
    'britishlike': ['british', 'french', 'irish'],
    'italianlike': ['greek', 'italian', 'mexican', 'spanish'],
    'southern_uslike': ['brazilian', 'british', 'cajun_creole', 'irish', 'jamaican', 'southern_us']
}
def make_group_features(scores, groups=groups):
    to_add = []
    for name, group in groups.items():
        series = scores[group].mean(axis='columns')
        series.name = name
        to_add.append(series)
    return pd.concat(to_add, axis='columns')


# In[ ]:


comparisons = [
    ('british', 'french'),
    ('british', 'irish'),
    ('french', 'italian'),
    ('greek', 'italian'),
    ('greek', 'moroccan'),
    ('indian', 'japanese'),
    ('italian', 'spanish'),
    ('thai', 'vietnamese'),
    
    ('brazilian', 'southern_us'),
    ('british', 'southern_us'),
    ('cajun_creole', 'southern_us'),
    ('french', 'southern_us'),
    ('greek', 'southern_us'),
    ('irish', 'southern_us'),
    ('italian', 'southern_us'),
    ('jamaican', 'southern_us'),
    ('moroccan', 'southern_us'),
    ('mexican', 'southern_us'),
    ('russian', 'southern_us'),
    ('spanish', 'southern_us'),
    
    ('filipino', 'chinese'),
    ('indian', 'chinese'),
    ('japanese', 'chinese'),
    ('korean', 'chinese'),
    ('thai', 'chinese'),
    ('vietnamese', 'chinese'),
]
def make_comparison_features(scores, comparisons=comparisons):
    to_add = []
    for a, b in comparisons:
        series = scores[a] * scores[b].map(inverse)
        series.name = '-'.join([a, b])
        to_add.append(series)
    return pd.concat(to_add, axis='columns')


# In[ ]:


def plot_cnf(conf_matrix, classes):
    f, ax = plt.subplots(figsize=(9,9))
    sns.heatmap(conf_matrix, square=True, annot=True, fmt='d', cbar=False, cmap='Blues',
                xticklabels=classes, yticklabels=classes)
    plt.xlabel('predicted label')
    plt.ylabel('true label')


# In[ ]:


def save_output(output, prefix='temp_'):
    output = output.drop(columns=['ingredients', 'strings'])
    
    train = output.query('cuisine != "test"')
    test = output.query('cuisine == "test"')
    
    train.cuisine.to_csv('data/cuisine.csv', header=False, encoding='utf-8')
    
    train = train.drop(columns=['cuisine'])
    test = test.drop(columns=['cuisine'])
    
    train.to_csv('data/' + prefix + 'train.csv', header=True, encoding='utf-8') 
    test.to_csv('data/' + prefix + 'test.csv', header=True, encoding='utf-8')

