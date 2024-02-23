import os
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge

from datasets.dataset import Dataset
from models.naive_models import AverageYieldModel
from models.sklearn_model import SklearnModel
from config import PATH_DATA_DIR


def test_average_yield_model():
    model = AverageYieldModel(group_cols=["COUNTY_ID"], label_col="YIELD")
    data_path = os.path.join(PATH_DATA_DIR, "data_US", "county_data")
    yield_csv = os.path.join(data_path, "YIELD_COUNTY_US.csv")
    yield_df = pd.read_csv(yield_csv, index_col=["COUNTY_ID", "FYEAR"])
    dataset = Dataset(yield_df, feature_dfs=[])
    filtered_df = yield_df[yield_df.index.get_level_values(0) == "AL_AUTAUGA"]
    expected_pred = filtered_df["YIELD"].mean()
    model.fit(dataset)
    test_data = {
        "COUNTY_ID": "AL_AUTAUGA",
        "FYEAR": 2018,
        "YIELD": yield_df.loc[("AL_AUTAUGA", 2018)]["YIELD"],
    }

    test_preds, _ = model.predict_item(test_data)
    assert np.round(test_preds[0], 2) == np.round(expected_pred, 2)


def test_sklearn_model():
    data_path = os.path.join(PATH_DATA_DIR, "data_US", "county_features")
    # Training dataset
    train_csv = os.path.join(data_path, "grain_maize_US_train.csv")
    train_df = pd.read_csv(train_csv, index_col=["COUNTY_ID", "FYEAR"])
    train_yields = train_df[["YIELD"]].copy()
    feature_cols = [c for c in train_df.columns if c != "YIELD"]
    train_features = train_df[feature_cols].copy()
    train_dataset = Dataset(train_yields, [train_features])

    # Test dataset
    test_csv = os.path.join(data_path, "grain_maize_US_train.csv")
    test_df = pd.read_csv(test_csv, index_col=["COUNTY_ID", "FYEAR"])
    test_yields = test_df[["YIELD"]].copy()
    test_features = test_df[feature_cols].copy()
    test_dataset = Dataset(test_yields, [test_features])

    # Model
    ridge = Ridge(alpha=0.5)
    model = SklearnModel(
        ridge,
        index_cols=["COUNTY_ID", "FYEAR"],
        feature_cols=feature_cols,
        label_col="YIELD",
    )
    model.fit(train_dataset)
    test_preds, _ = model.predict(test_dataset)
    assert test_preds.shape[0] == len(test_dataset)

    # Model with hyperparameter optimization
    fit_params = {
        "optimize_hyperparameters": True,
        "param_space": {"estimator__alpha": [0.01, 0.1, 0.0, 1.0, 5.0, 10.0]},
    }
    model.fit(train_dataset, **fit_params)
    test_preds, _ = model.predict(test_dataset)
    assert test_preds.shape[0] == len(test_dataset)