import pandas as pd
import tushare as ts
import time


def run():
    # 注册基本款即可，基础积分每分钟内最多调取500次
    tushare_token = '397f0943992055890a89081cfe70d2e7b6563da7f3c2661cbe6db0e7'
    ts.set_token(tushare_token)
    pro = ts.pro_api()
    today = time.strftime("%Y%m%d", time.localtime(time.time()))
    df = pro.daily(trade_date=today)
    stock_list = pro.query('stock_basic', exchange='', list_status='L',
                           fields='ts_code,name')
    df = pd.merge(df, stock_list, on='ts_code')
    limit = df.loc[((round(df['pre_close'] * 1.07, 2) <= df['close']) & (
            (df['ts_code'].str.startswith('60')) | (df['ts_code'].str.startswith('0')))) |
                   ((round(df['pre_close'] * 1.15, 2) <= df['close']) & (df['ts_code'].str.startswith('300'))) |
                   ((round(df['pre_close'] * 1.03, 2) <= df['close']) & (df['name'].str.contains("ST")) & (
                           (df['ts_code'].str.startswith('60')) | (df['ts_code'].str.startswith('0'))))
                   ]
    concept = pd.read_csv('concept.csv')
    con_vol = dict()
    for i in concept.to_dict('records'):
        for j in i['concept'].split(','):
            if j in con_vol:
                con_vol[j] += 1
            else:
                con_vol[j] = 1
    concept = pd.merge(limit, concept, on='ts_code')
    concept = concept[['ts_code', 'name', 'concept', 'business', 'q_np_change']]
    concept.to_csv('hotspot.csv', index=False, encoding='utf-8-sig')
    con_dict = concept.to_dict('records')
    cp = dict()
    for i in con_dict:
        for j in i['concept'].split(','):
            if j in cp:
                cp[j].append(i['ts_code'] + i['name'])
            else:
                cp[j] = [i['ts_code'] + i['name']]
    import math
    # 给予孤儿概念惩罚系数
    cp_w = {k: len(cp[k]) / con_vol[k] * math.log(con_vol[k], 10) for k in cp}
    import networkx as nx
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    G = nx.Graph()
    mid = list(set([cp_w[k] for k in cp_w]))
    mid.sort()
    print(cp_w)
    num_of_concepts = 30
    for k in cp_w:
        if cp_w[k] >= mid[-num_of_concepts:][0]:
            G.add_edge(0, k, color='r', weight=cp_w[k])
    pos = nx.circular_layout(G, scale=2)
    pos[0] = np.array([0, 0])
    edges, weights = zip(*nx.get_edge_attributes(G, 'weight').items())
    nx.draw(G, pos, node_color=None, edgelist=edges, edge_color=weights, width=5.0, with_labels=True,
            edge_cmap=plt.cm.Blues, node_size=1000)
    plt.show()


if __name__ == '__main__':
    run()
