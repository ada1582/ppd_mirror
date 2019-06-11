## 数据情况

| 表名 | 内容 | 备注 |
| ------ | ------ | ------ |
| train | 训练集 |  |
| test | 测试集 |  |
| listing_info | 标的属性 |  |
| user_info | 用户信息 |  |
| user_taglist | 用户画像 |  |
| user_behavior_logs | 用户行为SDK |  |
| user_repay_logs | 还款日志 |  |

##特征工程

###Y
* 33类 多分类问题 未还款-1 还款0~31
* 9类 多分类问题 未还款-1 /当天还款 一/ 1 2 3二/4 5 6 7三/8 9 10 11 四/12 13 14 15五/
16 17 18 19六/20 21 22 23七/24 25 26 27 八/28 29 30 31 九
* 3类 多分类问题 未还款/当天还款/提前还款
* 二分类问题 是否在账单日还款
* 二分类问题 是否逾期

##### 策略
以33类/9类为基础，覆盖是否账单日还款/是否逾期，覆盖用户画像/可能的工资日等规则

----------------
### train/test
* 近3月订单数
* 近3月订单金额最大值
* 近3月订单金额均值
* 近3个月提前还款日期均值
* 近3个月提前还款日期最小值
* 近3个月提前还款日期最大值
* 近6月订单数
* 近6月订单数金额最大值
* 近6月订单金额均值
* 近6个月提前还款日期均值
* 近6个月提前还款日期最小值
* 近6个月提前还款日期最大值
* 近9月订单数
* 近9月订单数金额最大值
* 近9月订单金额均值
* 近9个月提前还款日期均值
* 近9个月提前还款日期最小值
* 近9个月提前还款日期最大值
* 是否有首逾记录
* max/min/skew/std/kurtosis
* 每天还款金额
* 当前金额占3/6/9均值比例

* 账单日据1/5/6/10/15/16/20/21/25/26天数差
* 账单日前1/5/6/10/15/16/20/21/25/26星期几

### listing_info
* 用户当前标的属性（期数，费率，总金额）
* 用户近3个月标的期数均值、最大值、最小值，方差
* 用户近3个月标的费率均值、最大值、最小值，方差
* 用户近3个月标的总金额均值、最大值、最小值，方差
* 用户近6个月标的期数均值、最大值、最小值，方差
* 用户近6个月标的费率均值、最大值、最小值，方差
* 用户近6个月标的总金额均值、最大值、最小值，方差
* 用户近9个月标的期数均值、最大值、最小值，方差
* 用户近9个月标的费率均值、最大值、最小值，方差
* 用户近9个月标的总金额均值、最大值、最小值，方差
* 用户近12个月标的期数均值、最大值、最小值，方差
* 用户近12个月标的费率均值、最大值、最小值，方差
* 用户近12个月标的总金额均值、最大值、最小值，方差
* 历史借款距当前最小天/最大天

### user_info
* 性别、年龄、身份证省、id省
* 身份证和id是否同一个省
* 注册时间据放款时间的月数

### user_taglist 
* 多少个不同的用户画像

根据tag建立逾期规则

### user_behavior_logs
* 用户近7天行为数
* 用户近7天行为1数、2数、3数

* 用户近1天行为数
* 用户近1天行为1数、2数、3数
* 用户近15天行为数
* 用户近15天行为1数、2数、3数
* 用户近30天行为数
* 用户近30天行为1数、2数、3数


### user_repay_logs
* 用户历史所有订单还款平均时间，若平均时间逾期则不还钱概率大，若平均时间超过一个月则算作工作日还款，
若平均时间在一月以内则认为是发工资日还款
* 平均还款时间
* 历史逾期次数
* 历史订单数
* 历史1/2/3期账单还款时间
* 100天内最近一次账单还款时间/金额
* 周1/5/6/7还款次数
* 1/5/6/10/11/15/16/20/21/25/26日还款次数
* 1/2/3月还款信息，本期账单与历史的比例

(似乎效果不好，用户更倾向于按照截止日期还款，而不是每月固定时间)

### other多表聚合特征
当前账单占历史账单比例


