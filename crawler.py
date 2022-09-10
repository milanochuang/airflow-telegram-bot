from bs4 import BeautifulSoup
import datetime
import os
# import rapidjson as json
import re
import requests

def search_for_video(inputSTR):
    base = "https://pttplay.cc/search.html?wd={}".format(inputSTR)
    r = requests.get(base)
    page = BeautifulSoup(r.text, "html.parser")
    resultLIST = []
    for i in page.find_all("a", href=True):
        regex = "<a href=\"(\/vod\/\d+.html)\" title=\"\S+\">(\S+)</a>"
        string = str(i)
        if re.match(regex, string):
            resultDICT = {
                "title": re.match(regex, string).group(2),
                "url": "https://pttplay.cc{}".format(re.match(regex, string).group(1))
                }
            resultLIST.append(resultDICT)
    return resultLIST

def find_video_url(inputURL):
    r = requests.get(URL)
    resultLIST = []
    page = BeautifulSoup(r.text, "html.parser")
    url = page.find("ul", {"id": "con_playlist_2"}).find_all("a", href=True)
    for i in url:
        resultLIST.append("https://pttplay.cc{}".format(i['href']))
    return resultLIST
if __name__== "__main__":
    URL = "https://pttplay.cc/vod/217320.html"
    r = requests.get(URL)
    reusltLIST = []
    page = BeautifulSoup(r.text, "html.parser")
    url = page.find("ul", {"id": "con_playlist_2"}).find_all("a", href=True)
    for i in url:
        print("https://pttplay.cc{}".format(i['href']))