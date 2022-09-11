from bs4 import BeautifulSoup
import datetime
import os
# import rapidjson as json
import re
import requests

def search_for_video(inputSTR):
    """
    return:
        [{'title': '魔戒：力量之戒第一季', 'url': 'https://pttplay.cc/vod/217320.html'},
        {'title': '魔戒二部曲：雙城奇謀', 'url': 'https://pttplay.cc/vod/13716.html'},
        {'title': '魔戒三部曲：王者再臨', 'url': 'https://pttplay.cc/vod/13687.html'},
        {'title': '魔戒首部曲：魔戒現身', 'url': 'https://pttplay.cc/vod/13695.html'},
        {'title': '戀愛秘籍之換體魔戒', 'url': 'https://pttplay.cc/vod/192544.html'},
        {'title': '魔戒', 'url': 'https://pttplay.cc/vod/187282.html'},
        {'title': '魔戒再現', 'url': 'https://pttplay.cc/vod/90844.html'},
        {'title': '牙狼：魔戒烈傳', 'url': 'https://pttplay.cc/vod/134036.html'},
        {'title': '顏值魔戒', 'url': 'https://pttplay.cc/vod/83849.html'}]
    """
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
    # print(resultLIST)
    return resultLIST

def find_video_url(inputURL):
    """
    return:
        {'episode': 1, 'url': 'https://pttplay.cc/v/217320-2-1.html'}
        {'episode': 2, 'url': 'https://pttplay.cc/v/217320-2-2.html'}
        {'episode': 3, 'url': 'https://pttplay.cc/v/217320-2-3.html'}
    """
    r = requests.get(inputURL)
    resultLIST = []
    page = BeautifulSoup(r.text, "html.parser")
    url = page.find("ul", {"id": "con_playlist_2"}).find_all("a", href=True)
    for i in url:
        resultDICT = {
            "episode": int(i.text),
            "url": "https://pttplay.cc{}".format(i['href'])
        }
        resultLIST.append(resultDICT)
    return resultLIST

if __name__== "__main__":
    search_for_video("海賊王")