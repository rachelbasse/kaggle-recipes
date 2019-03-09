# ['What's Cooking?' Kaggle Competition](https://www.kaggle.com/c/whats-cooking-kernels-only)

## Problem

This is a multiclass classification problem. Each datapoint is a recipe, which is simply a list of ingredients, e.g.:

```python
['Bertolli® Classico Olive Oil', 'boneless skinless chicken breast halves', 'eggs',
 'rigatoni or large tube pasta', 'chicken broth', 'bacon, crisp-cooked and crumbled', 
 'bertolli vineyard premium collect marinara with burgundi wine sauc',
 'bread crumb fresh', 'shredded mozzarella cheese']
```

The task is to classify each recipe as one of 20 cuisine classes:

```python
['brazilian', 'british', 'cajun_creole', 'chinese', 'filipino', 'french', 'greek', 'indian',
 'irish', 'italian', 'jamaican', 'japanese', 'korean', 'mexican', 'moroccan', 'russian',
 'southern_us', 'spanish', 'thai', 'vietnamese']
```

The training set contains 39,774 labeled datapoints. The final test set contains 9,944 datapoints (labels witheld). The sole metric for the competition is the accuracy score on the final test set.

## Solution

Three main featuresets were developed with 20, ~200, and ~2,000 features each, which scored 76.8%, 80.6%, and 81.9% accuracy, respectively. The highest score in the competition at close was 82.8%.

### Data Cleaning

1. **Basic character replacement.** All characters were lowercased and encoding errors (`â€™`) and non-word symbols were removed.
1. **Spelling correction.** A custom frequency dictionary was generated to retain the many rare, non-English words (e.g., `doubanjiang`) and regional spelling variations (e.g., `yoghurt` in `indian` cuisines) while correcting apparent errors (e.g., `sauc` => `sauce`).
1. **Word segmentation.** Potential segmentation inconsistencies were detected via word-length and changed to favor segmentation (e.g., `almondmilk` => `almond milk`).
1. **Brand extraction.** Brand names were detected via position, capitalization, and copyright/trademark characters and were marked as brands to permit special treatment.
1. **State-word extraction.** Words representing ingredient quality or state-changes (e.g., `large`, `freshly ground`, `diced`) were detected via POS tagging as adverbs, adjectives, or verbs and marked as state-words to permit special treatment.
1. **Lemmatization**. To reduce lemmatization errors, all words were treated as nouns when lemmatized. Stopwords were also removed.
1. **Head identification.** To permit special treatment of ingredient heads, prepositional-phrase complements and similar sub-phrases were moved to inital position to leave the head in the final position (e.g., `tomato sauce with garlic` => `garlic tomato sauce`).
1. **Modifier sorting.** Modifiers were sorted to increase consistency (e.g., `{red hot chile pepper, red chile hot pepper, hot red chile pepper, ...}` => `chile hot red pepper`).
1. **Head supertype addition.** With the help of scraped Wikipedia lists, common supertypes were appended to phrases to increase consistency and add information (e.g., `{jalapeno, jalapeno pepper}` => `jalapeno pepper`; `{assam, assam tea}` => `assam tea`).
1. **Language detection.** Language detection was performed with Google Translate, and language markers were added (e.g., `amchur powder` => `_lang-indian amchur powder`; `strozzapreti pasta` => `_lang-italian strozzapreti pasta`). English markers were omitted since they were the dominant type.
1. **Multiple representation.** Each recipe was stored in two forms: 1) as a string, e.g., `chile hot red pepper` and 2) as a list of modifier-head pairs, e.g., `[chile-pepper, hot-pepper, red-pepper]`.


### Features

The basic 20 features were created by assigning each recipe a score for each cuisine class. A recipe's score was simply the mean of the scores of its ingredients. An ingredient's score was meant to measure the frequency and importance of that ingredient in each cuisine, a variation on tf-idfs. Scores were generated as follows:

1. Count how many times each ingredient appears in each cuisine. E.g., the counts for `salt` and `mirin` in `japanese` cuisine were `430` and `402`, respectively.
1. Scale ingredient counts by cuisine recipe counts to account for the varying number of recipes for each cuisine (recipe counts range from 7,838 `italian` recipes to 467 `brazilian` recipes). E.g., the rates for `salt` and `mirin` in `japanese` cuisine were `.30` and `.28`, respectively.
1. Scale ingredient rates by the sum of the rates over all cuisines, yielding a proportional rate to reflect how important/discriminative each ingredient is. E.g., `salt` appears at a high rate in all cuisines (`.26`-`.65`), for a sum total of `9.48`. The proportional rate for `salt` in `japanese` cuisine is thus `.30 / 9.48 = .03`. In contrast, `mirin` is very rare outside of `japanese` cuisine. The sum of its rates for all cuisines is `.37`, making its proportional rate in `japanese` cuisine `.28 / .37 = .75`, indicating that `mirin` is a much stronger signal of `japanese` cuisine than `salt` is, despite `salt` appearing slighlty more frequently.
1. Smooth/reweight proportional rates to balance false-positive and false-negative confusions. E.g., there were 1546 `cajun_creole` recipes. Before reweighting, classifying a recipe as the class with the maximum score resulted in (IIRC) ~2400 false positives and only ~20 false negatives for the `cajun_creole` class. This was presumed to indicate that, for several possible reasons, many or most of the scores for the `cajun_creole` class were too high. All `cajun_creole` scores were thus decreased until the number of confusions was approximately balanced; in this case, the final `cajun_creole` confusions were 352 false-positives and 341 false-negatives. The specific smoothing formula was chosen after some testing, with the aim of preventing any single ingredient's score from dominating the mean: `a * log(1.01 + (x / (b + x)))`.

The next ~200 features were variations on this idea. E.g., scores were made from only ingredients (no brands, states, or language markers), from only the lowest- and highest-scoring ingredients, etc.

Additionally, (sorted) 2-length combinations of ingredients were used instead of ingredients, e.g., the recipe `[egg, flour, salt, water]` => `[egg+flour, egg+salt, egg+water, flour+salt, flour+water, salt+water]`.

The final ~2000 features included normal tf-idf scores, using only {0,1} as the term-frequencies.

Several other features, such as recipe length, as well as various recipe-score calculations, were tested and rejected.

### Models

Around a dozen classifiers were initially tested. Four of the best-performing classifiers (SVM, logistic regression, random forest, and nearest neighbors) were stacked via softmax voting and final SVM and logistic regression classifiers using the stacked models' probabilities as features. The best-performing stacking option varied with the featuresets.

Additionally, min-max ([0-1]) feature scaling and conservative over-sampling via SMOTE were performed. A custom SVM weighted RBF kernel was faked via a custom transformer that reweighted (upscaled) the most important features (as determined by random forests and PCA) prior to fitting.

Hyperparameters were tuned on folds of the training data. I suspect some leakage occurred during cross-validation since the cleaning and feature-extraction processes incorporated information from the entire training set and were not written to integrate with scikit-learn's pipeline and cross-validation tools, which I used. (It slipped my mind initially that I didn't have the labels for the test set.) Fixing this will be the first thing on my to-do list if I have time to work on this more, with the hope that stopping the leakage will allow me to find more optimal hyperparameters.

