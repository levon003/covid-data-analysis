import numpy as np
import pandas as pd
import pytest

import covid_modeling.modeling


def get_feature_df(n_true, n_false):
    n = n_true + n_false

    target = pd.Series(data=np.zeros(n), dtype="float32", name="target")
    target[:n_true] = 1
    feature_df = pd.DataFrame(target, index=target.index)

    true_idx = feature_df.target == 1
    assert true_idx.sum() == n_true

    rng = np.random.default_rng()

    feature = rng.normal(size=n)
    feature_df["a"] = feature
    feature = rng.normal(size=n)
    feature[true_idx] += 5 * np.abs(rng.normal(size=n_true))
    feature_df["b"] = feature
    return feature_df


@pytest.mark.parametrize(
    "use_l2",
    [True, False],
)
def test_fit_predict_logit(use_l2):
    train_df = get_feature_df(100, 100)
    test_df = get_feature_df(100, 100)
    preds, model = covid_modeling.modeling.fit_predict_logit(train_df, test_df, formula="target ~ a + b", l2=use_l2)
    assert model is not None
    assert len(preds) == len(test_df)


def test_evaluate_models():
    df = get_feature_df(10000, 10000)
    formula_list = [
        ("noint", "target ~ a + b"),
        ("int", "target ~ a + b + a*b"),
        ("a_only", "target ~ a"),
        ("b_only", "target ~ b"),
    ]
    results = covid_modeling.modeling.evaluate_models(df, formula_list, target_name="target")
    assert len(results) == 8
    result_df = pd.DataFrame(results)
    assert (
        result_df.groupby("model_name").size() == 2
    ).all(), "Every model should have been fit twice (with and without l2)"
    assert (result_df.loc[result_df.model_name == "b_only", "f1"] >= 0.8).all()
    assert (result_df.loc[result_df.model_name == "a_only", "f1"] < 0.6).all()


def test_evaluate_models_exception():
    df = get_feature_df(10, 10)
    formula_list = [("test", "target ~ b")]
    _ = covid_modeling.modeling.evaluate_models(df, formula_list, target_name="target")
