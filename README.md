# kaggle-recipes


## Clean Data

1. Spelling correction
1. Word segmentation
1. Extract states, brands
1. heads, mods
1. mods in order
1. language detection

# Make Features

1. Add 2-length combinations for strings and parts
1. Make counts
1. Remove rare ingredients
1. Scale by number of recipes to get rates
1. Take proportion of rates
1. Reweight/smooth proportions to get points - until confusion types equal
1. Take mean score for each recipe for each cuisine
1. Variations on same idea: raw scores, low/top ings, ranks, std ranks, ovr ratios
1. recipe length, lengths of ings
1. group east/west, individual ratios

# Select Models

1. over-sampling w/ smote
1. so many classifiers
1. hyperparameter tuning
1. stacking via voting, lrc, dtc/rfc
1. not worth it: easy round first/reduced classes, train on high-prob test, when uncertain choose 2nd, easy/hard classifiers
