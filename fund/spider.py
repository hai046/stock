#!/usr/bin/python
# -*- coding: UTF-8 -*-
import json
import sqlite3

import requests


class Eastmoney:

    def __init__(self):
        self.__con = sqlite3.connect('eastmoney.db')
        self.__cur = self.__con.cursor()
        self.__cur.executescript(
            '''
            create table if not exists eastmoney_list
               (
                   code text not null,
                   name text not null,
                   holder_company_num long not null,
                   holder_sum long not null,
                   holder_value long not null,
                   type text not null,
                   change_value long not null,
                   change_rate float not null ,
                   change_date date,
                   unique(code,change_date)
               );
            ''')
        self.__cur.executescript(
            '''
         create table if not exists eastmoney_holder_detail
        (
            indtCode   string,
            instSName  string,
            rDate      date not null,
            sCode      string,
            code       string,
            sHCode     string,
            sHName     string,
            SName      string,
            shareHDNum long,
            tabProRate float,
            tabRate    float,
            `type`       string,
            typeCode   int,
            vposition  long,
            unique(code,indtCode,SHCode,rDate)
        );
            ''')

        self.__con.commit()

    def __del__(self):
        self.__con.commit()

    def start(self):
        fd = self.__get_data_list()
        self.__parse(fd)
        print()

    def __get_data_list(self):
        url = 'http://datapc.eastmoney.com/emdatacenter/jgcc/getdatelist'
        response = requests.get(url)
        if response.status_code != 200:
            print("request url=", url + "  err", response.status_code)
            return None
        list = json.loads(response.content)
        print(list)
        if len(list) > 0:
            return list[0]

        return None
        pass

    def __parse(self, fd, page=1, max=10000):
        if page > max:
            return
        url = 'http://datapc.eastmoney.com/emdatacenter/jgcc/list?fd=%s&stat=1&st=2&sr=-1&p=%s&ps=50&cmd=1' % (
            fd, page)
        print(url)
        response = requests.get(url)
        if response.status_code != 200:
            print("request url=", url + "  err", response.status_code)
            return
        payload = json.loads(response.content)
        self.__cur.execute("")
        print(url)
        for item in payload['data']:
            sql = "insert  into  eastmoney_list(`code`,`name`,`holder_company_num`,`holder_sum`,`holder_value`,`type`,`change_value`,`change_rate`,`change_date` )" \
                  "values ({0[0]},'{0[1]}',{0[2]},{0[3]},{0[4]},'{0[5]}',{0[6]},{0[7]},{0[8]}) ;".format(
                item)
            print(sql)
            try:
                self.__cur.execute(sql)
                self.__detail(item[0], item[8])
            except sqlite3.IntegrityError as e:
                continue
            self.__con.commit()

        if page < payload['pages']:
            self.__parse(fd, page + 1)
        pass

    pass

    def __detail(self, code, date, page=1):
        url = "http://datapc.eastmoney.com/emdatacenter/JGCC/getHoldDetail"
        response = requests.post(url, data={
            'stat': 0,
            'scode': '',
            'code': code,
            'date': date,
            'item': 2,
            'sr': -1,
            'pageIndex': page,
            'pageSize': 30,
        })
        if response.status_code != 200:
            print("request url=", url + "  err", response.status_code)
            return
        payload = json.loads(response.content)

        for item in payload['data']:
            sql = "insert into     eastmoney_holder_detail (indtCode, instSName, rDate,sCode,code,sHCode ,sHName,SName,shareHDNum ,tabProRate,tabRate , `type`,typeCode ,vposition)" \
                  "values ('{0[0]}','{0[1]}','{0[2]}','{0[3]}','{1}','{0[4]}','{0[5]}','{0[6]}',{0[7]},{0[8]},{0[9]},'{0[10]}',{0[11]},{0[12]}) "
            json_items = ["IndtCode",
                          "InstSName",
                          "RDate",
                          "SCode",
                          "SHCode",
                          "SHName",
                          "SName",
                          "ShareHDNum",
                          "TabProRate",
                          "TabRate",
                          "Type",
                          "TypeCode",
                          "Vposition"
                          ]

            values = []
            for name in json_items:
                values.append(item[name])
            sql = sql.format(values, str(item['SCode']).split(".")[0])
            # print(sql)
            try:
                self.__cur.execute(sql)
            except sqlite3.IntegrityError as e:
                print()

        if page < payload['totalpage']:
            self.__detail(code, date, page + 1)
        pass


if __name__ == '__main__':
    em = Eastmoney()
    em.start()
