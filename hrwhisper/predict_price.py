# -*- coding: utf-8 -*-
# @Date    : 2017/10/31
# @Author  : hrwhisper
"""
    Given a user feature, predict the price. the predicted price will be use as a feature for predicting shop_id.
"""
import os

import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.externals import joblib
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import KFold

from common_helper import ModelBase
from parse_data import read_train_join_mall, read_test_data
from use_location import LocationToVec
from use_location2 import LocationToVec2

from use_time import TimeToVec
from use_wifi import WifiToVec


class CategoryPredicted(ModelBase):
    def __init__(self):
        super().__init__()
        self.feature_save_path = './feature_save/predicted_price.csv'

    def _get_classifiers(self):
        """
        :return: dict. {name:classifier}
        """
        return {
            'RandomForestRegressor ': RandomForestRegressor(n_estimators=100, n_jobs=4)
        }

    def train_test(self, vec_func, target_column='price', fold=5):
        """

        :param vec_func: list of vector function
        :param target_column: the target column you want to predict.
        :param fold: the fold of cross-validation.
        :return: None
        """
        # ------input data -----------
        _train_data = read_train_join_mall()
        _train_data = _train_data.sort_values(by='time_stamp')
        _train_label = _train_data[target_column].values
        _test_data = read_test_data()

        kf = KFold(n_splits=fold, random_state=self._random_state)
        oof_train = np.zeros((_train_data.shape[0],))
        oof_test = np.zeros((_test_data.shape[0],))
        oof_test_skf = np.zeros((fold, _test_data.shape[0]))

        for i, (train_index, test_index) in enumerate(kf.split(_train_data)):
            fold_X_train, fold_y_train = _train_data.iloc[train_index], _train_label[train_index]
            fold_X_test, fold_y_test = _train_data.iloc[test_index], _train_label[test_index]

            self._trained_and_predict(vec_func, fold_X_train, fold_y_train, fold_X_test, fold_y_test, _test_data,
                                      oof_train, oof_test_skf, i)

        oof_test[:] = oof_test_skf.mean(axis=0)

        joblib.dump(oof_train, self.feature_save_path + '_oof_train.pkl', compress=3)
        joblib.dump(oof_test, self.feature_save_path + '_oof_test.pkl', compress=3)

        with open(self.feature_save_path, 'w') as f:
            f.write('row_id,price\n')
            for i, row_id in enumerate(_train_data['row_id']):
                f.write('{},{}\n'.format(row_id, oof_train[i]))
            for i, row_id in enumerate(_test_data['row_id']):
                f.write('{},{}\n'.format(row_id, oof_test[i]))
        print('done')

    def _trained_and_predict(self, vec_func, fold_X_train, fold_y_train, fold_X_test, fold_y_test, R_X_test,
                             oof_train, oof_test, cur_fold):
        clf = list(self._get_classifiers().values())[0]
        for ri, mall_id in enumerate(fold_X_train['mall_id'].unique()):
            X_train, y_train, X_test, y_test = self._train_and_test_to_vec(mall_id, vec_func, fold_X_train,
                                                                           fold_y_train, fold_X_test, fold_y_test)

            clf.fit(X_train, y_train)
            predicted = clf.predict(X_test)

            oof_train[fold_X_test.index[fold_X_test['mall_id'] == mall_id]] = predicted
            score = mean_squared_error(y_test, predicted)
            print(ri, mall_id, score)

            X_test, _ = self._data_to_vec(mall_id, vec_func, R_X_test, None, is_train=False)
            oof_test[cur_fold, R_X_test.index[R_X_test['mall_id'] == mall_id]] += clf.predict(X_test)


def train_test():
    task = CategoryPredicted()
    func = [LocationToVec2(), WifiToVec(), TimeToVec()]
    task.train_test(func, 'price')
    task.train_and_on_test_data(func, 'price')


def recovery_price_from_pkl():
    _train_data = read_train_join_mall()
    _train_data = _train_data.sort_values(by='time_stamp')
    _test_data = read_test_data()

    oof_train = joblib.load('./feature_save/predicted_price.csv_oof_train.pkl')
    oof_test = joblib.load('./feature_save/predicted_price.csv_oof_test.pkl')
    with open('./feature_save/predicted_price.csv', 'w') as f:
        f.write('row_id,p_price\n')
        for i, row_id in enumerate(_train_data['row_id']):
            f.write('{},{}\n'.format(row_id, oof_train[i]))
        for i, row_id in enumerate(_test_data['row_id']):
            f.write('{},{}\n'.format(row_id, oof_test[i]))


if __name__ == '__main__':
    # train_test()
    recovery_price_from_pkl()