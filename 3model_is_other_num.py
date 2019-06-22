# -*- coding: utf-8 -*-
# @Author: limeng
# @File  : 3model_is_other_num.py
# @time  : 2019/6/14
"""
文件说明：二分类问题，对于其他天数的训练1~31
"""
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error, log_loss, accuracy_score
import gc

date = "0619"
# oripath = "F:/数据集/1906拍拍/"
# inpath = "F:/数据集处理/1906拍拍/"
# outpath = "F:/项目相关/1906拍拍/out/"
oripath = "/home/dev/lm/paipai/ori_data/"
inpath = "/home/dev/lm/paipai/feature/"
outpath = "/home/dev/lm/paipai/out/"

df_basic = pd.read_csv(open(inpath + "feature_basic.csv", encoding='utf8'))
print("feature_basic",df_basic.shape)
df_train = pd.read_csv(open(inpath + "feature_basic_train{}.csv".format(date), encoding='utf8'))
print("feature_basic_train",df_train.shape)
df_behavior_logs = pd.read_csv(open(inpath + "feature_behavior_logs{}.csv".format(date), encoding='utf8'))
print("feature_behavior_logs",df_behavior_logs.shape)
df_listing_info = pd.read_csv(open(inpath + "feature_listing_info{}.csv".format(date), encoding='utf8'))
print("feature_listing_info",df_listing_info.shape)
df_repay_logs = pd.read_csv(open(inpath + "feature_repay_logs{}.csv".format(date), encoding='utf8'))
print("feature_repay_logs",df_repay_logs.shape)
df_user_info_tag = pd.read_csv(open(inpath + "feature_user_info_tag{}.csv".format(date), encoding='utf8'))
print("feature_user_info_tag",df_user_info_tag.shape)
df_other = pd.read_csv(open(inpath + "feature_other{}.csv".format(date), encoding='utf8'))
print("feature_other",df_other.shape)
#合并所有特征
df = df_basic.merge(df_train,how='left',on=['user_id','listing_id','auditing_date'])
df = df.merge(df_behavior_logs,how='left',on=['user_id','listing_id','auditing_date'])
df = df.merge(df_listing_info,how='left',on=['user_id','listing_id','auditing_date'])
df = df.merge(df_repay_logs,how='left',on=['user_id','listing_id','auditing_date'])
df = df.merge(df_user_info_tag,how='left',on=['user_id','listing_id','auditing_date'])
df = df.merge(df_other,how='left',on=['user_id','listing_id','auditing_date'])
print(df.shape)
#调整多分类y
df["y_date_diff"] = df["y_date_diff"].replace(-1,32) #0~31
df["y_date_diff_bin"] = df["y_date_diff_bin"].replace(-1,9)
df["y_date_diff_bin3"] = df["y_date_diff_bin3"].replace(-1,2)

train = df[df["auditing_date"]<='2018-12-31']
train['repay_amt'] = train['repay_amt'].apply(lambda x: x if x != '\\N' else 0).astype('float32')
train["y_date_diff"]=train["y_date_diff"].astype(int)
train["y_date_diff_bin"]=train["y_date_diff_bin"].astype(int)
train["y_date_diff_bin3"]=train["y_date_diff_bin3"].astype(int)
test = df[df["auditing_date"]>='2019-01-01']
print(train.shape)
print(test.shape)
# 字符变量处理

#无法入模的特征和y
del_feature = ["user_id","listing_id","auditing_date","due_date","repay_date","repay_amt"
                ,"user_info_tag_id_city","user_info_tag_taglist","dead_line",
               "other_tag_pred_is_overdue", "other_tag_pred_is_last_date",
                "user_info_tag_id_province", "user_info_tag_cell_province"]
y_list = [i  for i in df.columns if i[:2]=='y_']
del_feature.extend(y_list)
features = []
for col in df.columns:
    if col not in del_feature:
        features.append(col)
# catgory_feature = ["auditing_month","user_info_tag_gender","user_info_tag_cell_province","user_info_tag_id_province",
#                    "user_info_tag_is_province_equal"]
catgory_feature = ["auditing_month","user_info_tag_gender", "user_info_tag_is_province_equal"]
model_n = []
loss = []
auc = [] # 5+过拟合
for i in range(32):
    if i == 0:
        continue
    print(i)
    y = "y_is_{}".format(i)

    #开始训练
    from sklearn.model_selection import StratifiedKFold, KFold
    from sklearn.metrics import mean_squared_error
    from sklearn.metrics import log_loss,roc_auc_score
    import lightgbm as lgb
    import numpy as np

    # 5~29有问题 0.73661 0.73924 0.73958 max_depth改为4
    if i in [1,2,3,4,5,28,29,30,31]:
        param = {'num_leaves': 2 ** 5,
                 'min_data_in_leaf': 32,
                 'objective': 'binary',
                 'max_depth': 5,
                 'learning_rate': 0.03,
                 "boosting": "gbdt",
                 "feature_fraction": 0.8,
                 "bagging_freq": 1,
                 "bagging_fraction": 0.8,
                 "bagging_seed": 11,
                 "metric": 'auc',
                 "lambda_l1": 0.5,
                 "verbosity": -1,
                 'is_unbalance': True
                 }
    else:
        param = {'num_leaves': 2 ** 4,
                 'min_data_in_leaf': 32,
                 'objective': 'binary',
                 'max_depth': 4, #5
                 'learning_rate': 0.03,
                 "boosting": "gbdt",
                 "feature_fraction": 0.8,
                 "bagging_freq": 1,
                 "bagging_fraction": 0.8,#0.8
                 "bagging_seed": 11,
                 "metric": 'auc',
                 "lambda_l1": 0.5,
                 "verbosity": -1,
                 'is_unbalance': True
                 }
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=2333)
    # folds = KFold(n_splits=5, shuffle=True, random_state=2333)
    oof = np.zeros(len(train))
    predictions = np.zeros(len(test))
    feature_importance_df = pd.DataFrame()

    for fold_, (trn_idx, val_idx) in enumerate(folds.split(train[features], train[y].values)):
        print("fold {}".format(fold_))
        trn_data = lgb.Dataset(train.iloc[trn_idx][features],
                               label=train[y].iloc[trn_idx],
                               categorical_feature=catgory_feature)
        val_data = lgb.Dataset(train.iloc[val_idx][features],
                               label=train[y].iloc[val_idx],
                               categorical_feature=catgory_feature)

        num_round = 5000
        clf = lgb.train(param, trn_data, num_round, valid_sets=[trn_data, val_data], verbose_eval=50,
                        early_stopping_rounds=100,categorical_feature=catgory_feature)

        oof[val_idx] = clf.predict(train.iloc[val_idx][features], num_iteration=clf.best_iteration)

        fold_importance_df = pd.DataFrame()
        fold_importance_df["feature"] = features
        fold_importance_df["importance"] = clf.feature_importance()
        fold_importance_df["fold"] = fold_ + 1
        feature_importance_df = pd.concat([feature_importance_df, fold_importance_df], axis=0)

        predictions += clf.predict(test[features], num_iteration=clf.best_iteration) / folds.n_splits

    print("CV score: {:<8.5f}".format(log_loss(train[y].values, oof)))
    print("auc score:",roc_auc_score(train[y].values, oof))
    feature_importance = feature_importance_df[["feature", "importance"]].groupby("feature").mean().sort_values(by="importance",
    ascending=False)

    feature_importance.to_csv(outpath+"importance_is_{}_{}.csv".format(i,date))
    #测试集逾期概率
    test_dic = {
        "user_id": test["user_id"].values,
        "listing_id":test["listing_id"].values,
        "auditing_date":test["auditing_date"].values,
        "due_amt":test["due_amt"].values,
    }
    test_prob = pd.DataFrame(test_dic)
    test_prob["is_{}".format(i)] = predictions
    test_prob.to_csv(outpath+"is_{}_{}.csv".format(i,date),index=None)
    model_n.append(i)
    loss.append(log_loss(train[y].values, oof))
    auc.append(roc_auc_score(train[y].values, oof))

model_loss = pd.DataFrame({"model":model_n,"loss":loss,"auc":auc})
model_loss.to_csv(outpath+"auc_model1_31_{}.csv".format(date))

