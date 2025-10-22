#!/usr/bin/env python3
# coding: utf-8
# File: data_spider.py
# Author: lhy<lhy_in_blcu@126.com,https://huangyong.github.io>
# Date: 18-10-3
# Modified: 添加并发症爬取和随机代理功能


import urllib.request
import urllib.parse
from lxml import etree
import pymongo
import re
import random
import time

"""基于司法网的犯罪案件采集"""


class CrimeSpider:
    def __init__(self):
        self.conn = pymongo.MongoClient()
        self.db = self.conn["medical"]
        self.col = self.db["data"]
        self.proxies = self.get_proxies()  # 初始化代理池

    """获取代理IP池"""

    def get_proxies(self):
        """从代理网站获取代理IP，这里使用示例代理，实际使用时可替换为代理API"""
        proxies = [
            "http://111.177.189.148:9000",
            "http://113.121.249.185:9999",
            "http://123.163.96.122:9999",
            # 可添加更多代理
        ]

        # 验证代理有效性
        valid_proxies = []
        for proxy in proxies:
            if self.validate_proxy(proxy):
                valid_proxies.append(proxy)
                print(f"有效代理: {proxy}")

        return (
            valid_proxies if valid_proxies else proxies
        )  # 如果没有有效代理，使用原始列表

    """验证代理有效性"""

    def validate_proxy(self, proxy):
        try:
            proxy_handler = urllib.request.ProxyHandler({"http": proxy})
            opener = urllib.request.build_opener(proxy_handler)
            opener.addheaders = [
                (
                    "User-Agent",
                    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.63 Safari/537.36",
                )
            ]
            urllib.request.install_opener(opener)
            response = urllib.request.urlopen("http://httpbin.org/ip", timeout=5)
            return response.getcode() == 200
        except:
            return False

    """随机获取一个代理"""

    def get_random_proxy(self):
        if not self.proxies:
            self.proxies = self.get_proxies()  # 重新获取代理池
        return random.choice(self.proxies)

    """根据url，请求html，使用随机代理"""

    def get_html(self, url):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/51.0.2704.63 Safari/537.36"
        }

        # 最多尝试3次获取页面
        for _ in range(3):
            try:
                proxy = self.get_random_proxy()
                proxy_handler = urllib.request.ProxyHandler({"http": proxy})
                opener = urllib.request.build_opener(proxy_handler)
                opener.addheaders = list(headers.items())
                req = urllib.request.Request(url=url)
                res = opener.open(req, timeout=10)
                html = res.read().decode("gbk")
                return html
            except Exception as e:
                print(f"使用代理 {proxy} 请求失败: {e}，尝试更换代理...")
                # 从代理池移除无效代理
                if proxy in self.proxies:
                    self.proxies.remove(proxy)
                time.sleep(1)  # 等待1秒后重试

        # 如果所有代理都失败，尝试不使用代理
        try:
            req = urllib.request.Request(url=url, headers=headers)
            res = urllib.request.urlopen(req, timeout=10)
            html = res.read().decode("gbk")
            return html
        except Exception as e:
            print(f"不使用代理请求失败: {e}")
            return ""

    """url解析"""

    def url_parser(self, content):
        selector = etree.HTML(content)
        urls = [
            "http://www.anliguan.com" + i
            for i in selector.xpath('//h2[@class="item-title"]/a/@href')
        ]
        return urls

    """并发症信息爬取"""

    def accompany_spider(self, url):
        html = self.get_html(url)
        if not html:
            return []

        selector = etree.HTML(html)
        # 并发症通常在特定标签中，这里根据实际页面结构调整XPath
        accompanies = selector.xpath(
            '//*[contains(@class, "jib-articl")]//span[contains(@class, "db")]//a'
        )

        # 清洗数据
        accompanies = [
            accompany.strip() for accompany in accompanies if accompany.strip()
        ]
        return accompanies

    """测试"""

    def spider_main(self):
        for page in range(1, 11000):
            try:
                basic_url = "http://jib.xywy.com/il_sii/gaishu/%s.htm" % page
                cause_url = "http://jib.xywy.com/il_sii/cause/%s.htm" % page
                prevent_url = "http://jib.xywy.com/il_sii/prevent/%s.htm" % page
                symptom_url = "http://jib.xywy.com/il_sii/symptom/%s.htm" % page
                inspect_url = "http://jib.xywy.com/il_sii/inspect/%s.htm" % page
                treat_url = "http://jib.xywy.com/il_sii/treat/%s.htm" % page
                food_url = "http://jib.xywy.com/il_sii/food/%s.htm" % page
                drug_url = "http://jib.xywy.com/il_sii/drug/%s.htm" % page
                accompany_url = (
                    "http://jib.xywy.com/il_sii/neopathy/%s.htm" % page
                )  # 并发症URL

                data = {}
                data["url"] = basic_url
                data["basic_info"] = self.basicinfo_spider(basic_url)
                data["cause_info"] = self.common_spider(cause_url)
                data["prevent_info"] = self.common_spider(prevent_url)
                data["symptom_info"] = self.symptom_spider(symptom_url)
                data["inspect_info"] = self.inspect_spider(inspect_url)
                data["treat_info"] = self.treat_spider(treat_url)
                data["food_info"] = self.food_spider(food_url)
                data["drug_info"] = self.drug_spider(drug_url)
                data["accompany"] = self.accompany_spider(
                    accompany_url
                )  # 添加并发症信息

                print(page, basic_url)
                self.col.insert(data)

            except Exception as e:
                print(e, page)
        return

    """基本信息解析"""

    def basicinfo_spider(self, url):
        html = self.get_html(url)
        selector = etree.HTML(html)
        title = selector.xpath("//title/text()")[0]
        category = selector.xpath('//div[@class="wrap mt10 nav-bar"]/a/text()')
        desc = selector.xpath('//div[@class="jib-articl-con jib-lh-articl"]/p/text()')
        ps = selector.xpath('//div[@class="mt20 articl-know"]/p')
        infobox = []
        for p in ps:
            info = (
                p.xpath("string(.)")
                .replace("\r", "")
                .replace("\n", "")
                .replace("\xa0", "")
                .replace("   ", "")
                .replace("\t", "")
            )
            infobox.append(info)
        basic_data = {}
        basic_data["category"] = category
        basic_data["name"] = title.split("的简介")[0]
        basic_data["desc"] = desc
        basic_data["attributes"] = infobox
        return basic_data

    """treat_infobox治疗解析"""

    def treat_spider(self, url):
        html = self.get_html(url)
        selector = etree.HTML(html)
        ps = selector.xpath('//div[starts-with(@class,"mt20 articl-know")]/p')
        infobox = []
        for p in ps:
            info = (
                p.xpath("string(.)")
                .replace("\r", "")
                .replace("\n", "")
                .replace("\xa0", "")
                .replace("   ", "")
                .replace("\t", "")
            )
            infobox.append(info)
        return infobox

    """treat_infobox治疗解析"""

    def drug_spider(self, url):
        html = self.get_html(url)
        selector = etree.HTML(html)
        drugs = [
            i.replace("\n", "").replace("\t", "").replace(" ", "")
            for i in selector.xpath('//div[@class="fl drug-pic-rec mr30"]/p/a/text()')
        ]
        return drugs

    """food治疗解析"""

    def food_spider(self, url):
        html = self.get_html(url)
        selector = etree.HTML(html)
        divs = selector.xpath('//div[@class="diet-img clearfix mt20"]')
        try:
            food_data = {}
            food_data["good"] = divs[0].xpath("./div/p/text()")
            food_data["bad"] = divs[1].xpath("./div/p/text()")
            food_data["recommand"] = divs[2].xpath("./div/p/text()")
        except:
            return {}

        return food_data

    """症状信息解析"""

    def symptom_spider(self, url):
        html = self.get_html(url)
        selector = etree.HTML(html)
        symptoms = selector.xpath('//a[@class="gre" ]/text()')
        ps = selector.xpath("//p")
        detail = []
        for p in ps:
            info = (
                p.xpath("string(.)")
                .replace("\r", "")
                .replace("\n", "")
                .replace("\xa0", "")
                .replace("   ", "")
                .replace("\t", "")
            )
            detail.append(info)
        symptoms_data = {}
        symptoms_data["symptoms"] = symptoms
        symptoms_data["symptoms_detail"] = detail
        return symptoms, detail

    """检查信息解析"""

    def inspect_spider(self, url):
        html = self.get_html(url)
        selector = etree.HTML(html)
        inspects = selector.xpath('//li[@class="check-item"]/a/@href')
        return inspects

    """通用解析模块"""

    def common_spider(self, url):
        html = self.get_html(url)
        selector = etree.HTML(html)
        ps = selector.xpath("//p")
        infobox = []
        for p in ps:
            info = (
                p.xpath("string(.)")
                .replace("\r", "")
                .replace("\n", "")
                .replace("\xa0", "")
                .replace("   ", "")
                .replace("\t", "")
            )
            if info:
                infobox.append(info)
        return "\n".join(infobox)

    """检查项抓取模块"""

    def inspect_crawl(self):
        for page in range(1, 3685):
            try:
                url = "http://jck.xywy.com/jc_%s.html" % page
                html = self.get_html(url)
                data = {}
                data["url"] = url
                data["html"] = html
                self.db["jc"].insert(data)
                print(url)
            except Exception as e:
                print(e)


handler = CrimeSpider()
handler.spider_main()  # 注意：原代码最后调用的是inspect_crawl，这里改为spider_main以测试主要功能
