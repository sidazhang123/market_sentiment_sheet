# 市场情绪监控表
# 每次盘后（16：00？）运行，首次运行对当日涨停个股，向前递归统计连板高度

# 红色代表普涨，绿色代表普跌，蓝色代表空间板（3连以上），灰色代表休市日
# 日期          红盘 绿盘 最终涨停 最终跌停 炸板（日k的high&close比较） 1连板 2连板 3连板 个股（3连，股名+行业） 3连板以上 个股（股名+连板高度+行业）
# 2020-01-01   3234 299  63       13            5                22   15    4    xx-券商，...         2      xx-4-建筑，...
# 2020-01-02 ......
from get_k_data import get_k_data
from rw_sheet import write
import pandas as pd


def run():
    # 注册基本款即可，基础积分每分钟内最多调取500次
    tushare_token = ''
    data = get_k_data(tushare_token)
    if not data.validate():
        write(data.today, info=None)
        return
    # 当日涨停df
    limit_u = data.get_limit(trade_date=data.today)
    # print(limit_u)
    limit_u_num = len(data.get_limit(trade_date=data.today))
    # 当日上涨数，下跌数，炸板数，跌停数
    u_num, d_num, boom_num, limit_d_num = data.get_current_info()
    # 代码:连板数
    limit_record = {i: 0 for i in limit_u['ts_code'].to_list()}
    # print(limit_record)
    # 计算连板
    last_b_date = data.today
    while True:
        last_b_date = data.get_last_b_date(last_b_date)
        # 内积排除断板

        limit_u = pd.merge(limit_u['ts_code'], data.get_limit(trade_date=last_b_date), on='ts_code')
        # print(limit_u)
        has_code = False
        for ts_code in limit_u['ts_code'].to_list():
            if ts_code in limit_record:
                limit_record[ts_code] = limit_record[ts_code] + 1
                has_code = True
        # print(limit_record)
        if not has_code: break

    # 代码:连板数->连板数：代码 -> 连板数：（股名，行业）
    _d = dict()
    for code in limit_record:
        row = data.stock_list.loc[data.stock_list['ts_code'] == code]
        name = row['name'].item()
        industry = row['industry'].item()
        if limit_record[code] in _d:
            _d[limit_record[code]].append((name, industry))
        else:
            _d[limit_record[code]] = [(name, industry)]
    _d.pop(0)
    limit_record = _d

    print("上涨{}家，下跌{}家，炸板{}个，跌停{}个，涨停{}个".format(u_num, d_num, boom_num, limit_d_num, limit_u_num))
    print('连板情况:')
    for i in limit_record:
        print("连{}板:".format(i))
        print(limit_record[i])
    write(data.today, info=[u_num, d_num, boom_num, limit_d_num, limit_u_num, limit_record])


if __name__ == '__main__':
    run()
