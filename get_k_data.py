import time
import tushare as ts
from datetime import datetime, timedelta
import pandas as pd

class get_k_data():
    def __init__(self, token):
        self.today = time.strftime("%Y%m%d", time.localtime(time.time()))
        # self.today='20210414'
        self.month_ago = datetime.today() - timedelta(days=31)
        self.token = token
        ts.set_token(self.token)
        self.pro = ts.pro_api()
        self.df = (None, '1970-01-01')

    # 检查是否开盘，交易日是否在4点后
    def validate(self) -> bool:
        trade_cal = self.pro.trade_cal(exchange='', start_date=self.month_ago.strftime('%Y%m%d'),
                                       end_date=self.today)
        self.trade_cal = trade_cal[trade_cal['is_open'] == 1]['cal_date'].to_list()
        if self.trade_cal[-1] == self.today:
            # 4点前没数据
            if datetime.now() < datetime.strptime(self.today + '16:00', '%Y%m%d%H:%M'):
                raise Exception('{} 还未到4点'.format(datetime.now().strftime('%H:%M')))
            self._get_stock_list()
            return True
        return False

    def _get_stock_list(self):
        self.stock_list = self.pro.query('stock_basic', exchange='', list_status='L',
                                         fields='ts_code,name,industry,list_date')

    def _get_data(self, trade_date):
        df = self.pro.daily(trade_date=trade_date)
        if df.empty: raise Exception('pro.daily returns empty')
        self.df = (df, trade_date)

    # 涨停df，只看10%的
    def get_limit(self, trade_date) -> pd.DataFrame:
        if self.df[1] != trade_date: self._get_data(trade_date)
        df = self.df[0]
        # 涨停，ret整个df算连板
        limit_u = df.loc[
            (round(df['pre_close']*1.1,2)==df['close']) & ((df['ts_code'].str.startswith('60')) | (df['ts_code'].str.startswith('0')))]
        # 1个月内新ipo不算
        limit_u = pd.merge(self.stock_list, limit_u, on='ts_code')
        return limit_u.loc[pd.to_datetime(limit_u['list_date'], format='%Y%m%d') < self.month_ago]

    # 上涨数，下跌数，炸板数，跌停数
    def get_current_info(self) -> tuple:
        # 跌停，ret当日跌停数
        df = self.df[0]
        limit_d = df.loc[
            (round(df['pre_close']*0.9,2)==df['close']) & ((df['ts_code'].str.startswith('60')) | (df['ts_code'].str.startswith('0')))]
        limit_d = pd.merge(self.stock_list, limit_d, on='ts_code')
        limit_d = limit_d.loc[pd.to_datetime(limit_d['list_date'], format='%Y%m%d') < self.month_ago]
        # 最高涨停收盘没有，炸板数(没封住都叫炸板)
        return len(df.loc[df['pct_chg'] > 0]), len(df.loc[df['pct_chg'] < 0]), len(
            df.loc[(round(df['pre_close'] * 1.1, 2) == df['high']) & (df['close'] < df['high'])]), len(limit_d)

    def get_last_b_date(self, date_str) -> str:
        for i, d in enumerate(self.trade_cal):
            if d == date_str: return self.trade_cal[i - 1]
        raise Exception('一个月的交易日历罩不住？')
