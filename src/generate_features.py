import pandas as pd
from sklearn.utils import resample
import numpy as np
from src.load_data import load_data
import logging
import argparse
import yaml
import os
import subprocess
import re
import boto3
import sqlalchemy

logger = logging.getLogger(__name__)



def get_target(df, target, **kwargs):
    """Gets values of target labels of the dataframe."""
    y = df['y']

    return y.values




def additional_processing(df, additional_processing_column = None, **kwargs):
    """
    Function that clean the column job, remove the trailing dot 
    
    Args:
        df (pandas.DataFrame object): data frame with irrevant predictors removed
    Returns:
        df (pandas.DataFrame object): data frame with trailing dots removed in cells 
    """

    if 'additional_processing_column' is not None:
        df[additional_processing_column] = df[additional_processing_column].replace('\.','', regex=True)
    else:
        raise ValueError("The column that needs extra cleaning has to be specified")

    return df


def balance_class(df):
    """
    Function that balances y.
    The response variable y is imbalanced with no:yes roughly equal to 9:1.
    This function down-samples the majority class by randomly removing observations
    from the majority class to prevent its signal from dominating the learning algorithm.
    Args:
        df (pandas.DataFrame object): data frame
    Returns:
        df_downsampled (pandas.DataFrame object): downsampled data frame
    """
    # separate observations from each class into different DataFrames
    # resample the majority class without replacement,
    # setting the number of samples to match that of the minority class
    # combine the down-sampled majority class DataFrame with the original minority class DataFrame.

    # Separate majority and minority classes
    df_majority = df[df.y == 'no']
    df_minority = df[df.y == 'yes']

    # Downsample majority class
    df_majority_downsampled = resample(df_majority,
                                       replace=False,  # sample without replacement
                                       n_samples=len(df_minority),  # to match minority class
                                       random_state=123)  # reproducible results

    # Combine minority class with downsampled majority class
    df_downsampled = pd.concat([df_majority_downsampled, df_minority])

    return df_downsampled


def reduce_no_of_class(df):
    """
    Function that reduce the number of classes for the month and bins numerical age variables into high, medium, and low
    
    Args:
        df (pandas.DataFrame object): data frame with irrevant predictors removed
    Returns:
        df (pandas.DataFrame object): data frame that has variable of month with 3 classes and age with 3 classes 
    """
    
    # classify month into 3 categories based on frequency count
    j = 0    
    for i in df['month']:
        if (i in ('may','jun','jul','aug')):
            df.iloc[j,10] = 'high'
        elif (i in ('feb','apr','nov')):
            df.iloc[j,10] = 'medium'
        else:
            df.iloc[j,10] = 'low'
        j = j+1
    
    # calculate the quantile of the age 
    c1 = df['age'].quantile(1/3)
    c2 = df['age'].quantile(2/3)

    # divide the age into 3 classes based on quantile 
    j = 0
    for i in df['age']:
        if (i < c1):
            df.iloc[j,0] = 'low'
        elif (c1 <=i<=c2 ):
            df.iloc[j,0] = 'medium'
        else:
            df.iloc[j,0] = 'high'
        j = j+1
    return df


    
    


def convert_types(df):
    """
    Function that converts categorical attributes to numerical factors
    that can be used in future model development.
    
    Args:
        df (pandas.DataFrame object): cleaned and undersampled data
    Returns:
        df (pandas.DataFrame object): data frame with only numbers
    """
    
    for col_name in list(df):
        if(df[col_name].dtype == 'object'):
            df[col_name]= df[col_name].astype('category')
            df[col_name] = pd.factorize(df[col_name])[0]
    return df






def choose_features(df, features_to_use=None, target=None, **kwargs):
    """Reduces the dataset to the features_to_use. Will keep the target if provided.
    Args:
        df (:py:class:`pandas.DataFrame`): DataFrame containing the features.
        features_to_use (:obj:`list`): List of columnms to extract from the dataset to be features.
        target (str, optional): If given, will include the target column in the output dataset as well.
    Returns:
        X (:py:class:`pandas.DataFrame`): DataFrame containing extracted features (and target, it applicable).
    """

    logger.debug("Choosing features")
    if features_to_use is not None:
        features = []
        dropped_columns = []
        for column in df.columns:
            # Identifies if this column is in the features to use or if it is a dummy of one of the features to use
            if column in features_to_use or column == target:
                features.append(column)
            else:
                dropped_columns.append(column)

        if len(dropped_columns) > 0:
            logger.info("The following columns were not used as features: %s", ",".join(dropped_columns))
        logger.debug(features)
        X = df[features]
    else:
        logger.debug("features_to_use is None, df being returned")
        X = df

    return X





def run_features(args):
    with open(args.config, "r") as f:
        config = yaml.load(f)

    # read the data file if given or using load_data function
    if args.input is not None:
        df = pd.read_csv(args.input)
    elif "load_data" in config:
        df = load_data(config["load_data"])
    else:
        raise ValueError("Path to CSV for input data must be provided through --csv or "
                         "'load_data' configuration must exist in config file")
        
    # perform all data processing    
    df = additional_processing(df, **config["generate_features"])
    df = balance_class(df)
    df = reduce_no_of_class(df)
    df = convert_types(df)
    df = choose_features(df, **config['generate_features']['choose_features'])
    
    if args.output is not None:
        df.to_csv(args.output, index=False)
        logger.info("Features saved to %s", args.output)

    return df









