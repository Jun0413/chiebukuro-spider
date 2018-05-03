###############################################################################
# author: zeng junhao
# created: 25/04/2018
# last-modified: 27/04/2018
#
###############################################################################

import sys
import json
import time
import datetime

import scrapy
from scrapy.http.request import Request
from six.moves.urllib import parse

class YahooQASpider(scrapy.Spider):
    
    name = "yahooQA_spider"

    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
        'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
        'scrapy_fake_useragent.middleware.RandomUserAgentMiddleware': 400,
        }
    } # employs a fake user agent


    def set_YMD(self):
        self.year = self.date.year
        self.month = self.date.month
        self.day = self.date.day


    def get_YDM_url(self):
        return self.base_url+"&year="+str(self.year)+"&month="+str(self.month)+"&day="+str(self.day)


    def initialize(self):
        # initialization
        self.counter = 0 # counts number of QA retrieved
        self.page = 1 # count number of QA pages touched

        self.date = datetime.date.today()
        self.set_YMD()

        self.category = "Smart device, PC, Electrical Appliances" # leave dummy here now 2080401469

        self.base_fn = "S-PC-EA_"
        self.base_url = "https://chiebukuro.yahoo.co.jp/dir/list.php?did=2080401469&flg=1&type=list&sort=3"

        self.fps = {} # since we got multiple threads, we need a stack of file pointers
        self.fps_counter = {} # corresponding counter dict to fps


    def start_requests(self):

        self.initialize()

        yield Request(
            url=self.get_YDM_url(),
            callback=self.extract_QA
        )


    def extract_QA(self, response):

        ##### block for testing #####
        # stops at 2018 some month
        if self.year == 2004 and self.month == 4 and self.day == 2:
            sys.exit()
        #############################

        links = response.xpath(".//ul[@id='qalst']/li/dl/dt/a/@href").extract()
        for url in links:
            yield Request(
                url=url,
                callback=self.parse_QA_page
            )

        next_link = response.xpath("//*[@id='yschnxtb']/a/@href").extract_first()
        if next_link:
            self.page += 1
            yield Request(
                url=next_link,
                callback=self.extract_QA
            )
        else:
            # update date
            self.date -= datetime.timedelta(days=1)
            self.set_YMD()

            yield Request(
                url=self.get_YDM_url(),
                callback=self.extract_QA
            )


    def parse_QA_page(self, response):

        qa_id = response.url.split('/')[-1] # such as q11189287016
        self.counter += 1

        date = response.xpath('//*[@id="main"]/div[1]/div[3]/div[2]/div[1]/div/p[2]/text()').extract_first().split("/")
        year = date[0]
        month = date[1]
        fn_key = year + "-" + month
        if fn_key in self.fps.keys():
            fp = self.fps[fn_key]
            self.fps_counter[fn_key] += 1
        else:
            fp = open(self.base_fn + fn_key + ".json", "w")
            fp.write("[")
            self.fps[fn_key] = fp
            self.fps_counter[fn_key] = 1
        if self.fps_counter[fn_key] > 1:
            fp.write(",\n")

        cat_path = '//*[@id="bcrmb"]/li[2]/a/span/text()'
        subcat_path = '//*[@id="bcrmb"]/li[3]/a/span/text()'
        subsubcat_path = '//*[@id="bcrmb"]/li[4]/a/span/text()'
        #que_path = ".//p[@class='yjDirectSLinkTarget']"
        que_path = "//*[@id='main']/div[1]/div[3]/div[2]/div[2]/p[1]/text()"
        desc_path = "//*[@id='main']/div[1]/div[3]/div[2]/div[2]/p[2]/text()"
        bestans_path = "//*[@id='ba']/div[1]/div[2]/div[2]/div[2]/p/text()"
        #bestans_path = "//*[@id='ba']//p[@class='queTxt yjDirectSLinkTarget']"
        othrans_path = "//div[@id='ans']//p[@class='queTxt']" # by me
        other_ans = []

        cat = self.merge_text(response.xpath(cat_path).extract(), qa_id, "cat")
        subcat = self.merge_text(response.xpath(subcat_path).extract(), qa_id, "subcat")
        subsubcat = self.merge_text(response.xpath(subsubcat_path).extract(), qa_id, "subsubcat")
        que = self.merge_text(response.xpath(que_path).extract(), qa_id, "que")
        desc = self.merge_text(response.xpath(desc_path).extract(), qa_id, "desc")
        bestans = self.merge_text(response.xpath(bestans_path).extract(), qa_id, "bestans")
        for otherans in response.xpath(othrans_path):
            other_ans.append(self.merge_text(otherans.xpath("./text()").extract(), qa_id, "other_ans"))
            
        fp.write(json.dumps({
            "qa_id": qa_id.strip(),
            "cat": cat.strip(),
            "sub_cat": subcat.strip(),
            "subsub_cat": subsubcat.strip(),
            "qn_title": que.strip(),
            "qn_desc": desc.strip(),
            "best_ans": bestans.strip(),
            "othr_ans": [oa.strip() for oa in other_ans]
        }, ensure_ascii=False))

    def merge_text(self, text_list, qa_id, step):
        if type(text_list) is list:
            return " ".join(text_list)
        elif type(text_list) is str:
            return text_list
        else:
            print("Failed to merge text at {0} for {1}".format(qa_id, step))
            raise Exception("Wrong extraction")

    def closed(self, reason):

        # close file pointers
        for key in self.fps.keys():
            self.fps[key].close()

        # validate json format
        for key in self.fps.keys(): # key is <year-month>
            fp = open(self.base_fn + key + ".json", "a")
            fp.write("]")
            fp.close()

        # log stats
        with open(self.base_fn + "log" + ".txt", "w") as fp:
            fp.write("##########################       LOGGING INFO       ############################\n")
            fp.write("Total number of pages retrieved: " + str(self.page-1) + "\n")

            for key in self.fps.keys():
                fp.write("Number of QAs in " + key + ": " + str(self.fps_counter[key]) + "\n")

            fp.write("Total number of QA retrieved: " + str(self.counter) + "\n")
            fp.write("################################################################################\n")
