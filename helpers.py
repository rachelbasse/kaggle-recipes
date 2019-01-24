#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# invert dicts
def invert_dict_singles(orig):
    new = {}
    for k, v in orig.items():
        new[v] = new.get(v, [])
        new[v].append(k)
    return new

def invert_dict_lists(orig):
    new = {}
    for k, vals in orig.items():
        for v in vals:
            new[v] = k
    return new


# In[ ]:


from operator import itemgetter

def make_freq_dict(word_counts):
    lines = []
    for word, freq in sorted(word_counts.items(), key=itemgetter(1), reverse=True):
        if freq > 4 and len(word) > 3:
            lines.append('{0} {1}\n'.format(word, freq))
    with open('data/frequency_dictionary.txt', 'w+', encoding='utf-8') as file:
        for line in lines:
            file.write(line)


# In[ ]:


from symspellpy.symspellpy import SymSpell, Verbosity

sym_spell = SymSpell(83000, 1, 7)
dictionary_path = 'data/frequency_dictionary.txt'
if not sym_spell.load_dictionary(dictionary_path, 0, 1):
    print("Dictionary file not found")

def correct_spelling(word):
    suggestions = sym_spell.lookup(word, Verbosity.TOP, 1)
    if not suggestions:
        return word
    return suggestions[0].term


# In[ ]:


counts = lambda df: df.apply(pd.Series.value_counts, axis=0)


# In[ ]:


def get_errors(X, y, model, sort_col=None):
    errors = []
    for i in range(X.shape[0]):
        obs = X.iloc[i:i+1]
        real = y.iloc[i]
        y_pred = model.predict(obs)
        if y_pred != [real]:
            errors.append(i)
    errs = pd.concat([X.iloc[errors], y.iloc[errors]], axis=1)
    print('Errors:', errs.shape[0])
    if sort_key:
        errs.sort_values(sort_col, inplace=True)
    return errs

