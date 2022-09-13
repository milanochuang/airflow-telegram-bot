from datetime import timedelta, datetime
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
import time
from airflow.operators.bash_operator import BashOperator
from crawler import search_for_video, find_video_url
import json
import os

default_args = {
    'owner': 'Milan',
    'depends_on_past': False,
    'start_date': datetime(2022,8,17),
    'email': ['milanochuang@gmail.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
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

        # update to latest chapter
        for series_id, series_info in dict(all_series_info).items():
            all_series_info[series_id]['previous_episode_num'] = series_info['latest_episode_num']

        with open(metadata_path, 'w') as fp:
            json.dump(all_series_info, fp, indent=4, ensure_ascii=False)

def check_series_info(**context):
    metadata = context['task_instance'].xcom_pull(task_ids='get_read_history')
    all_series_info = metadata
    anything_new = False
    seriesDICT = find_video_url



def fn_superman():
    print("取得使用者的閱讀紀錄")
    print("去影片網站看有沒有新的章節")
    print("跟紀錄比較，有沒有新連載？")

    # Murphy's Law
    accident_occur = time.time() % 2 > 1
    if accident_occur:
        print("\n天有不測風雲,人有旦夕禍福")
        print("工作遇到預期外狀況被中斷\n")
        return

    new_comic_available = time.time() % 2 > 1
    if new_comic_available:
        print("寄 Slack 通知")
        print("更新閱讀紀錄")
    else:
        print("什麼都不幹，工作順利結束")


with DAG('comic_app_v1', default_args=default_args) as dag:
    superman_task = PythonOperator(
        task_id='superman_task',
        python_callable=fn_superman
    )