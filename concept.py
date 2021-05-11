import pandas as pd
import tushare as ts
import time


def run():
    # 注册基本款即可，基础积分每分钟内最多调取500次
    tushare_token = ''
    ts.set_token(tushare_token)
    pro = ts.pro_api()
    today = time.strftime("%Y%m%d", time.localtime(time.time()))
    df = pro.daily(trade_date=today)
    stock_list = pro.query('stock_basic', exchange='', list_status='L',
                           fields='ts_code,name')
    df = pd.merge(df, stock_list, on='ts_code')
    # 主板上涨7%，创业15，st股3，可放宽到上涨或缩进到涨停
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
    cp_w = {k: len(cp[k]) / con_vol[k] * math.log(con_vol[k]-2 if con_vol[k]>2 else 1, 3.5) for k in cp}
    import networkx as nx
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams["figure.figsize"] = (7, 7)

    G = nx.Graph()
    median = list(set([cp_w[k] for k in cp_w]))
    median.sort()
    print(cp_w)
    num_of_concepts = 30 if len(median)>30 else len(median)
    labels = {}
    node_n = 0
    for i, k in enumerate(cp_w):
        if cp_w[k] >= median[-num_of_concepts:][0]:
            G.add_edge(0, i + 1, color='r', weight=cp_w[k])
            labels[i + 1] = k
            node_n += 1
    pos = nx.circular_layout(G, scale=0.5)
    pos[0] = np.array([0, 0])
    edges, weights = zip(*nx.get_edge_attributes(G, 'weight').items())

    nx.draw(G, pos, node_color=None, edgelist=edges, edge_color=weights, width=5.0, with_labels=False,
            edge_cmap=plt.cm.Blues, node_size=1000)
    t = nx.draw_networkx_labels(G, pos, labels, font_size=14)

    for i, i_tup in enumerate(t.items()): i_tup[1].set_rotation(i / node_n * 360.0)
    plt.title(today)
    # plt.show()
    plt.savefig(today + '.png', dpi=200, bbox_inches='tight', pad_inches=1.2)
    plt.close()


if __name__ == '__main__':
    run()
