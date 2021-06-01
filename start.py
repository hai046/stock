#!/usr/bin/python
# -*- coding: UTF-8 -*-
import base64
import codecs
import datetime
import hashlib
import json
import os
import time

import requests
import yaml
from selenium.common.exceptions import NoSuchElementException


class Shares:

    def __init__(self, conf='config.yml'):
        self.driver = None
        self.today = datetime.datetime.now().strftime('%H%M')
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
        name = param[0]
        当前价格 = float(param[3])
        titles = ['名字',
                  '今日开盘价',
                  '昨日收盘价',
                  '当前价格',
                  '今日最高价',
                  '今日最低价',
                  # '竞买价',
                  # '竞卖价',
                  # '成交的股票数',  # 由于股票交易以一百股为基本单位，所以在使用时，通常把该值除以一百；
                  # '成交金额',  # 单位为“元”，为了一目了然，通常以“万元”为成交金额的单位，所以通常把该值除以一万；
                  # '买一数量',  # 买一手至少有多少，一般是100股
                  # '买一报价'
                  ]
        date = param[30]
        time = param[31]
        # print(name, date, time)
        msg = '> '
        index = 0
        for title in titles:
            msg += "%s：\t%s\n" % (title, param[index])
            index += 1

        url = 'https://biz.finance.sina.com.cn/suggest/lookup_n.php?country=11&q=%s' % id
        print(url)
        msg += "\n\n[更多](%s)" % url
        money_total = 0
        for conf in configs:

            if 'want_buy_price' in conf:
                want_buy_price = conf['want_buy_price']
                if 当前价格 <= want_buy_price:
                    if self.__send_msg(conf, " ## 提示:%s  \n> 名字：%s\n编号：%s\n当前价格：%s\n期望价格：%s" % (
                            conf['alert_msg']['content'], name, id, 当前价格, want_buy_price)):
                        self.__parse_img(url, conf)
            else:
                count = conf['buy_count']
                alert_up = conf['alert_up']
                alert_down = conf['alert_down']
                buy_price = conf['buy_price']
                money = count * (当前价格 - buy_price)
                money_total += money
                if 当前价格 >= alert_up:
                    if self.__send_msg(conf, '## 股票：%s[%s]\n<font color="warning">涨了，涨了，涨了</font>\n> ' % (
                            name, id) + msg + "\n收益：%.2d" % money):
                        self.__parse_img(url, conf)
                elif 当前价格 < alert_down:
                    if self.__send_msg(conf,
                                       '## 股票：%s[%s]\n<font color="info">已经跌到你的设置的\n警戒线：%s\n当前价格：%s\n购买价格：%s</font>\n> ' % (
                                               name, id, alert_down, 当前价格, buy_price) + msg):
                        self.__parse_img(url, conf)

                if self.today == '1516' or self.today == '0930' or self.today == '1130':

                    if self.__send_msg(conf, "## 每日提示 购买价：%s，当前价：%s，收益率：%.2f%%\n%s" % (
                            buy_price, 当前价格, 100 * (当前价格 - buy_price) / buy_price, msg) + "\n收益：%.2d" % (money)):
                        self.__parse_img(url, conf)
        pass

    def __sameAsLastTime(self, dic):
        cache = '.cache.json'
        current_content = json.dumps(dic, ensure_ascii=False)
        if os.path.exists(cache):
            with open(cache) as f:
                content = f.read()
                if current_content is content:
                    return True

        with open(cache, "w") as f:
            f.write(current_content)
        return False

    def __send_msg(self, conf, msg):
        if self.__sameAsLastTime({"conf": conf, "msg": msg}):
            return False
        requests.post(url='https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=%s' % conf['alert_msg']['wechat'],
                      json={
                          "msgtype": "markdown",
                          "markdown": {
                              "content": msg,
                          }
                      })
        return True

    def __parse_img(self, url, conf, show=False):
        from selenium import webdriver

        if self.driver is None:
            options = webdriver.ChromeOptions()
            if not show:
                options.add_argument('headless')  # 设置不显示页面
                options.add_argument('--disable-dev-shm-usage')
            # options.add_argument("--disable-blink-features=AutomationControlled")
            # options.add_argument('blink-settings=imagesEnabled=false')
            options.add_argument('--no-sandbox')
            # options.add_argument('--disable-gpu')
            # mobileEmulation = {'deviceName': 'iPhone 6/7/8'}  # 设置手机环境
            # options.add_experimental_option('mobileEmulation', mobileEmulation)
            self.driver = webdriver.Chrome(chrome_options=options)
        self.driver.get(url)
        try:
            div = self.driver.find_element_by_xpath('/html/body/div[7]/div[3]/div[1]/div[1]/div[11]/div[1]/div')
            self.__send_img(conf, div.screenshot_as_png)

            # 日K
            self.driver.find_element_by_xpath(
                '/html/body/div[7]/div[3]/div[1]/div[1]/div[11]/div[1]/div/div[2]/div[1]/div/div[5]').click()
            time.sleep(5)
            div = self.driver.find_element_by_xpath('/html/body/div[7]/div[3]/div[1]/div[1]/div[11]/div[1]/div')
            self.__send_img(conf, div.screenshot_as_png)
        except NoSuchElementException as e:
            # ETF 分时
            div = self.driver.find_element_by_xpath('/html/body/div[6]/div[1]/div/div[7]/div/div[1]/div')
            self.__send_img(conf, div.screenshot_as_png)
            # 日K
            self.driver.find_element_by_xpath(
                '/html/body/div[6]/div[1]/div/div[7]/div/div[1]/div/div[3]/div/span[3]').click()
            time.sleep(5)
            div = self.driver.find_element_by_xpath('/html/body/div[6]/div[1]/div/div[7]/div/div[1]/div')
            self.__send_img(conf, div.screenshot_as_png)

    pass

    def __del__(self):
        if self.driver is not None:
            self.driver.close()

    def __send_img(self, conf, binbody):
        msg = base64.b64encode(binbody)
        md5 = hashlib.md5(binbody).hexdigest()
        requests.post(url='https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=%s' % conf['alert_msg']['wechat'],
                      json={
                          "msgtype": "image",
                          "image": {
                              "base64": str(msg, 'utf-8'),
                              "md5": md5
                          }
                      }
                      )
        pass

    def __equals(self, current_content, content):
        if len(current_content) == len(content):
            index = 0
            while index < len(current_content):
                if current_content[index] is not content[index]:
                    print(index, current_content[index], content[index])
                    return False
                index += 1
            return True
        return False
        pass


if __name__ == '__main__':
    s = Shares()
