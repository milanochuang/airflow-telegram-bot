from datetime import timedelta, datetime
import time
import json
import os
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.providers.telegram.operators.telegram import TelegramOperator
from airflow.operators.latest_only import LatestOnlyOperator
import requests
from bs4 import BeautifulSoup
import re


default_args = {
    'owner': 'Milan',
    'start_date': datetime(2100,1,1,0,0),
    'schedule_interval': '@daily',
    'retries': 2,
    'retry_delay': timedelta(minutes=1)
}

# define the DAG
dag = DAG(
    dag_id = 'id',
    default_args = default_args,
    description = 'description',
    schedule_interval = '@daily', # run every day
    catchup=False # do not perform a backfill of missing runs
)

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
        {'217320': {'title': '魔戒：力量之戒第一季', 'episode': 3, 'url': 'https://pttplay.cc/v/217320-2-3.html'}}
    """
    r = requests.get(inputURL)
    resultLIST = []
    page = BeautifulSoup(r.text, "html.parser")
    title = page.find("div", {"id": "zanpian-score"}).find("h1").text
    url = page.find("ul", {"id": "con_playlist_2"}).find_all("a", href=True)
    regex = "https://pttplay\.cc/vod/(\d+)\.html"
    seriesID = re.match(regex, inputURL).group(1)
    for i in url:
        resultDICT = {seriesID:
            {
                "title": title,
                "episode": int(i.text),
                "url": "https://pttplay.cc{}".format(i['href'])
            }
        }
        resultLIST.append(resultDICT)
    return resultLIST

def process_metadata(mode, **context):

    file_dir = os.path.dirname(__file__)
    metadata_path = os.path.join(file_dir, '../data/tv-series.json')
    if mode == 'read':
        with open(metadata_path, 'r') as fp:
            metadata = json.load(fp)
            print("Read History loaded: {}".format(metadata))
            return metadata
    elif mode == 'write':
        print("Saving latest series information..")
        _, all_series_info = context['task_instance'].xcom_pull(task_ids='check_series_info')

        # update to latest episode
        for series_id, series_info in dict(all_series_info).items():
            all_series_info[series_id]['previous_episode_num'] = series_info['latest_episode_num']

        with open(metadata_path, 'w') as fp:
            json.dump(all_series_info, fp, indent=4, ensure_ascii=False)

def check_series_info(**context):
    metadata = context['task_instance'].xcom_pull(task_ids='get_read_history')
    all_series_info = metadata
    anything_new = False
    for series_id, series_info in dict(all_series_info).items():
        # 找最新一集的集數
        menu_url = "https://pttplay.cc/vod/{}.html".format(series_id)
        seriesLIST = find_video_url(menu_url)
        series_name = seriesLIST[-1][series_id]['title']
        latest_episode_num = seriesLIST[-1][series_id]['episode']
        previous_episode_num = series_info['previous_episode_num']
        url = seriesLIST[-1][series_id]['url']
        # 更新資料以及確認是否有新集數
        all_series_info[series_id]['latest_episode_num'] = latest_episode_num
        all_series_info[series_id]['new_episode_available'] = latest_episode_num > previous_episode_num
        all_series_info[series_id]['url'] = url
        if all_series_info[series_id]['new_episode_available']:
            anything_new = True
            print("There are new episode for {}(latest: {})".format(series_name, latest_episode_num))

    if not anything_new:
        print("Nothing new now, prepare to end the workflow.")

    return anything_new, all_series_info

def decide_what_to_do(**context):
    anything_new, all_series_info = context['task_instance'].xcom_pull(task_ids='check_series_info')

    print("跟紀錄比較，有沒有新連載？")
    if anything_new:
        return 'yes_generate_notification'
    else:
        return 'no_do_nothing'

def get_token():
    file_dir = os.path.dirname(__file__)
    token_path = os.path.join(file_dir, '../data/credentials/telegram.json')
    with open(token_path, 'r') as fp:
        token = json.load(fp)['api_key']
        return token

def generate_message(**context):
    _, all_series_info = context['task_instance'].xcom_pull(task_ids='check_series_info')

    message = ''
    for series_id, series_info in all_series_info.items():
        if series_info['new_episode_available']:
            name = series_info['title']
            latest = series_info['latest_episode_num']
            prev = series_info['previous_episode_num']
            url = series_info['url']
            message += '{} 最新一集： {} 話（上次看到：{} 集）\n'.format(name, latest, prev)
            message += url + '\n\n'

    file_dir = os.path.dirname(__file__)
    message_path = os.path.join(file_dir, '../data/message.txt')
    with open(message_path, 'w') as fp:
        fp.write(message)

def get_message_text():
    file_dir = os.path.dirname(__file__)
    message_path = os.path.join(file_dir, '../data/message.txt')
    with open(message_path, 'r') as fp:
        message = fp.read()

    return message



with DAG('telegram_bot', default_args=default_args) as dag:

    # define tasks
    latest_only = LatestOnlyOperator(task_id='latest_only')

    get_read_history = PythonOperator(
        task_id='get_read_history',
        python_callable=process_metadata,
        op_args=['read'],
    )

    check_series_info = PythonOperator(
        task_id='check_series_info',
        python_callable=check_series_info,
    )

    decide_what_to_do = BranchPythonOperator(
        task_id='new_series_available',
        python_callable=decide_what_to_do,
    )

    update_read_history = PythonOperator(
        task_id='update_read_history',
        python_callable=process_metadata,
        op_args=['write'],
    )

    generate_notification = PythonOperator(
        task_id='yes_generate_notification',
        python_callable=generate_message,
    )

    send_notification = TelegramOperator(
        task_id = 'send_notification',
        telegram_conn_id = get_token(),
        chat_id = "5676650832",
        text = get_message_text()
    )


    do_nothing = EmptyOperator(task_id='no_do_nothing')

    # define workflow
    latest_only >> get_read_history
    get_read_history >> check_series_info >> decide_what_to_do
    decide_what_to_do >> generate_notification
    decide_what_to_do >> do_nothing
    generate_notification >> send_notification >> update_read_history