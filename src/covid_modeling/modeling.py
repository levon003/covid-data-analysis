import warnings

import numpy as np
import pandas as pd
import sklearn
import sklearn.linear_model
import sklearn.model_selection
import statsmodels.formula.api as smf
from tqdm import tqdm


def fit_predict_logit(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    formula: str = "covid_death ~ gender + race + age",
    l2: bool = False,
) -> tuple:
    """Fits a logistic regression model given the train/test dataframes and a particular formula.

    If L2 regularization is active, we use sklearn rather than statsmodels.

    Parameters
    ----------
    train_df : pd.DataFrame
        Training data
    test_df : pd.DataFrame
        Testing data, with the same columns as train_df
    formula : str, optional
        Modeling formula to use, by default "covid_death ~ gender + race + age"
    l2 : bool, optional
        If l2 regularization should be used, by default False

    Returns
    -------
    tuple
        The predictions and the model object.
    """
    md = smf.logit(formula=formula, data=train_df)
    if not l2:
        res = md.fit(disp=False, maxiter=50)
        preds = res.predict(test_df)
        return preds, res
    else:
        logreg = sklearn.linear_model.LogisticRegression(fit_intercept=False, solver="liblinear")
        logreg.fit(md.exog, md.endog)
        preds = logreg.predict(smf.logit(formula=formula, data=test_df).exog)
        return preds, logreg


def evaluate_models(
    hdf: pd.DataFrame,
    model_formulas: list[tuple[str, str]],
    target_name: str = "covid_death",
) -> list[dict]:
    """
    Evaluate a set of model parameterizations, returning a list of summary statistics for each model.

    Parameters
    ----------
    hdf : pd.DataFrame
        Dataframe to evaluate, presumed to be the hospitalizations dataframe (see `covid_modeling.io`).
    model_formulas : list[tuple[str, str]]
        List of (model_name, model_formula) tuples. model_formula uses Patsy syntax, to be passed directly to `statsmodels.formula.api.logit`.
    target_name : str, optional
        The column we are predicting, by default "covid_death"

    Returns
    -------
    list[dict]
        List of dictionaries with metadata recorded for each model.
        Keys: model_name, l2, f1, roc_auc
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # we are exploring models with lots of interactions in a small dataset;
        # we are almost certain to generate lots of non-invertible matrices

        hdf = hdf.sample(frac=1)
        results = []
        for model_name, model_formula in tqdm(model_formulas):
            for l2 in [False, True]:
                kfold = sklearn.model_selection.KFold(n_splits=20, shuffle=False)
                y_score = np.zeros(len(hdf))
                for train_index, test_index in kfold.split(hdf):
                    train_df = hdf.iloc[train_index]
                    test_df = hdf.iloc[test_index]
                    try:
                        preds, _ = fit_predict_logit(train_df, test_df, formula=model_formula, l2=l2)
                        y_score[test_index] = preds
                    except Exception:
                        y_score[test_index] = 0  # default to a majority-class prediction
                y_true = hdf[target_name]
                y_pred = (y_score >= 0.5).astype(int)
                f1_death = sklearn.metrics.f1_score(y_true, y_pred)
                roc_auc = sklearn.metrics.roc_auc_score(y_true, y_score)
                results.append(
                    {
                        "model_name": model_name,
                        "l2": l2,
                        "f1": f1_death,
                        "roc_auc": roc_auc,
                    },
                )
    return results
