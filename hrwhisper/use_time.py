# -*- coding: utf-8 -*-
# @Date    : 2017/10/25
# @Author  : hrwhisper


import numpy as np
from scipy.sparse import csr_matrix
from sklearn.ensemble import RandomForestClassifier
from sklearn.externals import joblib
from datetime import datetime
from common_helper import ModelBase, XXToVec

from use_location import LocationToVec
from use_wifi3 import WifiToVec3

"""
LocationToVec(), WifiToVec3(), TimeToVec()
RandomForestClassifier(class_weight='balanced',n_estimators=400, n_jobs=4,
              random_state=42) Mean: 0.909196793335719
            
RandomForestClassifier(class_weight='balanced',n_estimators=200, n_jobs=4,
              random_state=42) Mean: 0.9086988576400435
"""


class TimeToVec(XXToVec):
    def __init__(self):
        super().__init__('./feature_save/time_features_{}_{}.pkl', './feature_save/time_features_{}_{}.pkl')

    def _extract_feature(self, train_data):
        features = np.array([
            np.array([_time.isoweekday(),
                      _time.isoweekday() >= 6,  # Mean: 0.9109541149905104 0.9076093830826543
                      _time.hour // 6,  # 0.9110178129353056 0.907882340
                      # _time.hour // 5,  # 0.9070676933021364 0.9077367366607973
                      # _time.hour, #  0.9105093297197597  0.9070204350804165 0.9070565010851597(time//5)
                      ])
            for _time in map(lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M"), train_data['time_stamp'].astype('str'))
        ])
        features = csr_matrix(np.hstack([features, train_data[['longitude', 'latitude']]]))
        return features

    def train_data_to_vec(self, train_data, mall_id, renew=True, should_save=False):
        """
        :param data: pandas. train_data.join(mall_data.set_index('shop_id'), on='shop_id', rsuffix='_mall')
        :param mall_id: str
        :param renew: renew the feature
        :param should_save: bool, should save the feature on disk or not.
        :return: csr_matrix
        """
        if renew:
            train_data = train_data.loc[train_data['mall_id'] == mall_id]
            features = self._extract_feature(train_data)
            if should_save:
                joblib.dump(features, self.FEATURE_SAVE_PATH.format('train', mall_id))
        else:
            features = joblib.load(self.FEATURE_SAVE_PATH.format('train', mall_id))
        return features

    def test_data_to_vec(self, test_data, mall_id, renew=True, should_save=False):
        if renew:
            test_data = test_data.loc[test_data['mall_id'] == mall_id]
            features = self._extract_feature(test_data)
            if should_save:
                joblib.dump(features, self.FEATURE_SAVE_PATH.format('test', mall_id))
        else:
            features = joblib.load(self.FEATURE_SAVE_PATH.format('test', mall_id))
        return features


class UseTime(ModelBase):
    def __init__(self):
        super().__init__()

    def _get_classifiers(self):
        return {
            'random forest': RandomForestClassifier(n_jobs=4, n_estimators=200, random_state=self._random_state,
                                                    class_weight='balanced'),
        }


def train_test():
    task = UseTime()
    task.train_test([LocationToVec(), WifiToVec3(), TimeToVec()])
    # task.train_and_on_test_data([LocationToVec(), WifiToVec3(), TimeToVec()])


if __name__ == '__main__':
    train_test()
    # 2017-08-06 21:20
    # _time = datetime.strptime('2017-08-06 21:20', "%Y-%m-%d %H:%M")
    # print(_time.hour)
    # print(_time.weekday() >= 5)
    # print(type(_time.isoweekday()))
