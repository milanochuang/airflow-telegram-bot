from bs4 import BeautifulSoup
import datetime
import os
# import rapidjson as json
import re
import requests

if __name__== "__main__":
    URL = "https://pttplay.cc/vod/217320.html"
    r = requests.get(URL)
    reusltLIST = []
    page = BeautifulSoup(r.text, "html.parser")
    print(page)