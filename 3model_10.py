# -*- coding: utf-8 -*-
#@author: limeng
#@file: 3_model_9.py
#@time: 2019/6/9 19:57
"""
文件说明：整合特征建模,10分类
未还款-1 /当天还款 一/ 1 2 3二/4 5 6 7三/8 9 10 11 四/12 13 14 15五/
16 17 18 19六/20 21 22 23七/24 25 26 27 八/28 29 30 31 九
train 2018.1.1~2018.12.31
test 2019.2.1~2019.3.31
"""
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error, log_loss, accuracy_score

# oripath = "F:/数据集/1906拍拍/"
# inpath = "F:/数据集处理/1906拍拍/"
# outpath = "F:/项目相关/1906拍拍/out/"
oripath = "/data/dev/lm/paipai/ori_data/"
inpath = "/data/dev/lm/paipai/feature/"
outpath = "/data/dev/lm/paipai/out/"

df_basic = pd.read_csv(open(inpath + "feature_basic.csv", encoding='utf8'))
print(df_basic.shape)
df_train = pd.read_csv(open(inpath + "feature_basic_train.csv", encoding='utf8'))
print(df_train.shape)
df_behavior_logs = pd.read_csv(open(inpath + "feature_behavior_logs.csv", encoding='utf8'))
print(df_behavior_logs.shape)
df_listing_info = pd.read_csv(open(inpath + "feature_listing_info.csv", encoding='utf8'))
print(df_listing_info.shape)
df_repay_logs = pd.read_csv(open(inpath + "feature_repay_logs.csv", encoding='utf8'))
print(df_repay_logs.shape)
df_user_info_tag = pd.read_csv(open(inpath + "feature_user_info_tag.csv", encoding='utf8'))
print(df_user_info_tag.shape)
df_other = pd.read_csv(open(inpath + "feature_other.csv", encoding='utf8'))
print(df_other.shape)
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
                ,"user_info_tag_id_city","user_info_tag_taglist","dead_line"
            ,"y_date_diff","y_date_diff_bin","y_date_diff_bin3","y_is_overdue","y_is_last_date"]
features = []
for col in df.columns:
    if col not in del_feature:
        features.append(col)
catgory_feature = ["auditing_month","user_info_tag_gender","user_info_tag_cell_province","user_info_tag_id_province",
                   "user_info_tag_is_province_equal"]
y = "y_date_diff_bin"
n = 10#分类数量，和y有关
class_dic ={0:[0],
            1:[1,2,3],
            2:[4,5,6,7],
            3:[8,9,10,11],
            4:[12,13,14,15],
            5:[16,17,18,19],
            6:[20,21,22,23],
            7:[24,25,26,27],
            8:[28,29,30,31],
            9:[32]}
class_dic_num ={0:1,
            1:3,
            2:4,
            3:4,
            4:4,
            5:4,
            6:4,
            7:4,
            8:4,
            9:1}
#开始训练
from sklearn.model_selection import StratifiedKFold, KFold
from sklearn.metrics import mean_squared_error
from sklearn.metrics import log_loss
import lightgbm as lgb
import numpy as np

param = {'objective': 'multiclass',
         'num_class':n,
         'num_leaves': 34,
         'min_data_in_leaf': 25,
         'max_depth': 5,  # 7
         'learning_rate': 0.02,
         'lambda_l1': 0.13,
         "boosting": "gbdt",
         "feature_fraction": 0.85,
         'bagging_freq': 8,
         "bagging_fraction": 0.9,
         "metric": 'multi_logloss',
         "verbosity": -1,
         "random_state": 2333}

folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=2333)
# folds = KFold(n_splits=5, shuffle=True, random_state=2333)
amt_labels = train['repay_amt'].values  # 真实还款
amt_oof = np.zeros(train.shape[0])
oof = np.zeros((len(train),n))
predictions = np.zeros((len(test),n))
feature_importance_df = pd.DataFrame()

for fold_, (trn_idx, val_idx) in enumerate(folds.split(train[features], train[y].values)):
    print("fold {}".format(fold_))
    trn_data = lgb.Dataset(train.iloc[trn_idx][features],
                           label=train[y].iloc[trn_idx],
                           categorical_feature=catgory_feature)
    val_data = lgb.Dataset(train.iloc[val_idx][features],
                           label=train[y].iloc[val_idx],
                           categorical_feature=catgory_feature)

    num_round = 1500
    clf = lgb.train(param, trn_data, num_round, valid_sets=[trn_data, val_data], verbose_eval=50,
                    early_stopping_rounds=20,categorical_feature=catgory_feature)
    #n*10矩阵
    val_pred_prob_everyday = clf.predict(train.iloc[val_idx][features], num_iteration=clf.best_iteration)
    oof[val_idx] = val_pred_prob_everyday
    # 将y全部展开，用应还金额*预测概率，求mse/mae
    val_y = train[y].values[val_idx] #真实label
    val_due_amt = train[["due_amt"]].iloc[val_idx] #应还款
    val_pred_prob_today = [val_pred_prob_everyday[i][val_y[i]]/class_dic_num[val_y[i]] for i in range(val_pred_prob_everyday.shape[0])]#预测还款在应还日的概率

    val_pred_repay_amt = val_due_amt['due_amt'].values * val_pred_prob_today #应还日的预测还款

    val_repay_amt = amt_labels[val_idx]
    amt_oof[val_idx] = val_pred_repay_amt
    print('val rmse:', np.sqrt(mean_squared_error(val_repay_amt, val_pred_repay_amt)))
    print('val mae:', mean_absolute_error(val_repay_amt, val_pred_repay_amt))

    fold_importance_df = pd.DataFrame()
    fold_importance_df["Feature"] = features
    fold_importance_df["importance"] = clf.feature_importance()
    fold_importance_df["fold"] = fold_ + 1
    feature_importance_df = pd.concat([feature_importance_df, fold_importance_df], axis=0)

    predictions += clf.predict(test[features], num_iteration=clf.best_iteration) / folds.n_splits

print('cv rmse:', np.sqrt(mean_squared_error(amt_labels, amt_oof)))
print('cv mae:', mean_absolute_error(amt_labels, amt_oof))
print("CV score: {:<8.5f}".format(log_loss(train[y], oof)))
feature_importance = feature_importance_df[["Feature", "importance"]].groupby("Feature").mean().sort_values(by="importance",
ascending=False)
feature_importance.to_csv(outpath+"importance_10.csv")
#train
train_prob = pd.DataFrame(oof)
train_prob33 = pd.DataFrame()
train_dic = {
    "user_id": train["user_id"].values,
    "listing_id":train["listing_id"].values,
    "auditing_date":train["auditing_date"].values,
    "due_date":train["due_date"].values,
    "due_amt":train["due_amt"].values,
}
for key in train_dic:
    train_prob[key] = train_dic[key]
    train_prob33[key] = train_dic[key]
for i in range(n-1):
    train_prob[i] = train_prob[i]*train_prob["due_amt"]/class_dic_num[i]
for k in class_dic:
    for v in class_dic[k]:
        train_prob33[v] = train_prob[k]
#test
test_prob = pd.DataFrame(predictions)
test_prob33 = pd.DataFrame()
test_dic = {
    "user_id": test["user_id"].values,
    "listing_id":test["listing_id"].values,
    "auditing_date":test["auditing_date"].values,
    "due_date":test["due_date"].values,
    "due_amt":test["due_amt"].values,
}
for key in test_dic:
    test_prob[key] = test_dic[key]
    test_prob33[key] = test_dic[key]
for i in range(n-1):
    test_prob[i] = test_prob[i]*test_prob["due_amt"]/class_dic_num[i]
for k in class_dic:
    for v in class_dic[k]:
        test_prob33[v] = test_prob[k]
#对于训练集评价
def df_rank(df_prob, df_sub):
    for i in range(33):
        print('转换中',i)
        df_tmp = df_prob[['listing_id', i]]
        df_tmp['rank'] = i+1
        df_sub = df_sub.merge(df_tmp,how='left',on=["listing_id",'rank'])
        df_sub.loc[df_sub['rank']==i+1,'repay_amt']=df_sub.loc[df_sub['rank']==i+1,i]
    return df_sub[['listing_id','repay_amt','repay_date']]
#
# submission_train =pd.read_csv(open(inpath+"submission_train.csv",encoding='utf8'),parse_dates=["repay_date"])
# submission_train['rank'] = submission_train.groupby('listing_id')['repay_date'].rank(ascending=False,method='first')
# sub_train = df_rank(train_prob33, submission_train)
# sub_train = sub_train.merge(submission_train,how='left',on=['listing_id','repay_date'])
# print('mse_real:', mean_squared_error(sub_train['repay_amt_x'], sub_train['repay_amt_y']))
#提交
submission = pd.read_csv(open(oripath+"submission.csv",encoding='utf8'),parse_dates=["repay_date"])
submission['rank'] = submission.groupby('listing_id')['repay_date'].rank(ascending=False,method='first')
sub = df_rank(test_prob33, submission)
sub.to_csv(outpath+'sub_lgb_10_0613.csv',index=None)
