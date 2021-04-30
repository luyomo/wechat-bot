#!/usr/bin/python3

import requests, re, json
import urllib.parse
import urllib.request
requests.packages.urllib3.disable_warnings()
from texttable import Texttable

from html.parser import HTMLParser
from yomoPyCommon.db.PGBase import PGBase
from yomoPyCommon.message.wechat import wechat

class dogeTopPosition(HTMLParser, PGBase):
    def __init__(self, _dbConfig, _url):
        self.htmlUrl = _url

        self.startPrint=False
        self.index = 0
        self.nthTbl = 0
        self.col = 0
        self.rePercentage = re.compile('(.*)%')
        self.first = 5
        self.arrResult = []
        HTMLParser.__init__(self)
        PGBase.__init__(self, _dbConfig['name'], _dbConfig['user'], _dbConfig['host'], _dbConfig['password'])

    def run(self, _debug=False):
        # Fetch the HTML text from html
        self.__resetDB()
        self.__requestHtml()

        self.startPrint=False
        self.index     = 0
        self.nthTbl    = 0
        self.col       = 0

        self.feed(self.htmlText)

        self.commit()

        return self.publishMsg(_debug)

    def __requestHtml(self):
        self.htmlText = requests.get(self.htmlUrl, verify=False).text

    def __resetDB(self):
        self.executeQuery(f"delete from cryptonews.doge_positions where data_date::date = current_date")

    def __insert2DB(self, _addr, _percentage):
        self.executeQuery(f"insert into cryptonews.doge_positions(address, percentage) values('{_addr}', '{_percentage}')")

    def handle_starttag(self, tag, attrs):
        if tag == "tbody":
            self.nthTbl += 1
            if self.nthTbl == 2:
                self.startPrint = True

        if self.startPrint == True:
            #print("Encountered a start tag:", tag)
            if tag == "tr":
                self.index += 1
                self.col = 0
                self.arrResult = []
            if self.index >= self.first+1:
                self.startPrint = False

    def handle_endtag(self, tag):
        if len(self.arrResult) > 1:
            self.__insert2DB(self.arrResult[0], self.arrResult[1])
            self.arrResult = []

    def handle_data(self, data):
        if self.startPrint == True:
            self.col += 1
            if self.col == 2:
                self.arrResult.append(data)
            if self.rePercentage.match(data):
                self.arrResult.append(data)

    def publishMsg(self, _debug):
        __res = self.fetchiDataJson(f"""
            with tmp_data_date as (select distinct data_date, dense_rank() over (order by data_date desc ) as rowid,
            row_number() over ( partition by data_date order by replace(percentage, '%', '')::numeric desc) as rank,
            address, percentage
            from cryptonews.doge_positions)
            select case when t1.address = t2.address then substr(t1.address, 0, 4) || '..'
                        else substr(t1.address,0,4) || '..>\n' || substr(t2.address, 0, 4) || '..' end as address,
                  t1.percentage || '=>' || t2.percentage as changes
              from tmp_data_date  t1
        inner join tmp_data_date t2
                on t1.rowid = 2
               and t2.rowid = 1
               and t1.rank = t2.rank
        order by t1.rank""")

        __table = Texttable()
        __table.header(('address', 'percentage' ))
        for __row in __res: __table.add_row((__row['address'], __row['changes']))
        __msg = __table.draw()
        print(f"{__msg}")
        return __msg

if __name__ == "__main__":
    __topDoge = dogeTopPosition()
    __topDoge.run()
