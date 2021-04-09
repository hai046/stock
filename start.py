#!/usr/bin/python
# -*- coding: UTF-8 -*-
import codecs
import datetime

import requests
import yaml


class Shares:

    def __init__(self, conf='config.yml'):

        with codecs.open(conf, 'r', 'utf-8') as fp:
            config = yaml.safe_load_all(fp.read())
            self.config = config
            for item in config:
                for k in item:
                    self.start(k, item[k])

    def start(self, id, conf):
        url = 'http://hq.sinajs.cn/list=%s' % id

        response = requests.get(url)
        status_code = response.status_code
        if status_code != 200:
            print("获取数据失败")
            return
        content = response.text.split('"')[1]
        print(content)
        self.__parse(content.split(','), conf, id)

    def __parse(self, param, configs, id):
        # https://cloud.tencent.com/developer/article/1534790?from=information.detail.%E8%82%A1%E7%A5%A8%E5%AE%9E%E6%97%B6%E8%A1%8C%E6%83%85%E6%95%B0%E6%8D%AE%E6%8E%A5%E5%8F%A3
        # 0：”大秦铁路”，股票名字；
        # 1：”27.55″，今日开盘价；
        # 2：”27.25″，昨日收盘价；
        # 3：”26.91″，当前价格；
        # 4：”27.55″，今日最高价；
        # 5：”26.20″，今日最低价；
        # 6：”26.91″，竞买价，即“买一”报价；
        # 7：”26.92″，竞卖价，即“卖一”报价；
        # 8：”22114263″，成交的股票数，由于股票交易以一百股为基本单位，所以在使用时，通常把该值除以一百；
        # 9：”589824680″，成交金额，单位为“元”，为了一目了然，通常以“万元”为成交金额的单位，所以通常把该值除以一万；
        # 10：”4695″，“买一”申请4695股，即47手；
        # 11：”26.91″，“买一”报价；
        # 12：”57590″，“买二”
        # 13：”26.90″，“买二”
        # 14：”14700″，“买三”
        # 15：”26.89″，“买三”
        # 16：”14300″，“买四”
        # 17：”26.88″，“买四”
        # 18：”15100″，“买五”
        # 19：”26.87″，“买五”
        # 20：”3100″，“卖一”申报3100股，即31手；
        # 21：”26.92″，“卖一”报价
        # (22, 23), (24, 25), (26,27), (28, 29)分别为“卖二”至“卖四的情况”
        # 30：”2008-01-11″，日期；
        # 31：”15:05:32″，时间；
        print(len(param))
        name = param[0]
        当前价格 = float(param[3])
        titles = ['名字',
                  '今日开盘价',
                  '昨日收盘价',
                  '当前价格',
                  '今日最高价',
                  '今日最低价',
                  '竞买价',
                  '竞卖价',
                  '成交的股票数',  # 由于股票交易以一百股为基本单位，所以在使用时，通常把该值除以一百；
                  '成交金额',  # 单位为“元”，为了一目了然，通常以“万元”为成交金额的单位，所以通常把该值除以一万；
                  # '买一数量',  # 买一手至少有多少，一般是100股
                  # '买一报价'
                  ]
        date = param[30]
        time = param[31]
        # print(name, date, time)
        msg = ''
        index = 0
        for title in titles:
            msg += "%s：\t%s\n" % (title, param[index])
            index += 1
        today = datetime.datetime.now().strftime('%H%M')

        for conf in configs:
            alert_up = conf['alert_up']
            alert_down = conf['alert_down']
            if 当前价格 >= alert_up:
                self.__send_msg(conf, '## 股票：%s[%s]\n<font color="warning">涨了，涨了，涨了</font>\n> ' % (name, id) + msg)
            elif 当前价格 < alert_down:
                self.__send_msg(conf,
                                '## 股票：%s[%s]\n<font color="info">已经跌到你的设置的\n警戒线：%s\n当前价格：%s\n购买价格：%s</font>\n> ' % (
                                    name, id, alert_down, 当前价格, conf['buy_price']) + msg)

            if today == '1500' or today == '0901':
                buy_price = conf['buy_price']
                self.__send_msg(conf, "## 每日提示 购买价：%s，当前价：%s，收益率：%.2f%%\n%s" % (
                    buy_price, 当前价格, 100 * (当前价格 - buy_price) / buy_price, msg))
        pass

    def __send_msg(self, conf, msg):
        requests.post(url='https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=%s' % conf['alert_msg']['wechat'],
                      json={
                          "msgtype": "markdown",
                          "markdown": {
                              "content": msg,
                          }
                      })


if __name__ == '__main__':
    s = Shares()
