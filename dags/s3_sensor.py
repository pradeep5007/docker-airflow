"""
S3 Sensor Connection Test
"""

from airflow import DAG
from airflow.operators import SimpleHttpOperator, HttpSensor,   BashOperator, EmailOperator, S3KeySensor
from datetime import datetime, timedelta
from airflow.operators.python_operator import PythonOperator
import airflow

import pip
import time
import json
import io

BUCKET = 'textract-gs'
WATCH_DIR = 'file-watch-dir'
INPUT_DIR = 'input-doc'
OUTPUT_DIR = 'output'

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    "start_date": airflow.utils.dates.days_ago( 1 ),
    'email': ['something@here.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 5,
    'retry_delay': timedelta(minutes=5)
}

def process_text_analysis(bucket, document):
    print("Running Text Analysis ")
    pip.main(['install', "boto3"])
    time.sleep(5)
    import boto3

    # abc = boto3.client('textract')
    # print("Created the textract boto client 2")
    # response = abc.analyze_document(
    #     Document={'S3Object': {'Bucket': bucket, 'Name': document}},
    #     FeatureTypes=["TABLES"])
    # print("Printing response")
    # print(response)

        # read the file , process the file , move to file to in dir
    s3_connection = boto3.resource('s3')

    for f in s3_connection.Bucket('%s' % (BUCKET)).objects.filter(Prefix=WATCH_DIR):
        if '.png' in f.key:
            watch_file = f
            break
    # run analyze text if new file is to watch
    if watch_file:
        fname = watch_file.key.split('/')[-1]
        client = boto3.client('textract')
        stream_binary = io.BytesIO(watch_file.get()['Body'].read()).getvalue()
        response = client.analyze_document(Document={'Bytes': stream_binary}, FeatureTypes=["TABLES"])

        # write the result to output dir with json ext
        s3object = s3_connection.Object(BUCKET, ('%s/%s.json') % (OUTPUT_DIR, fname.split('.')[0]))
        s3object.put(
            Body=(bytes(json.dumps(response['Blocks']).encode('UTF-8')))
        )
        # move the file to other folder
        boto3.client('s3').put_object(Body=stream_binary, Bucket=BUCKET,
                                      Key=('%s/%s') % (INPUT_DIR, watch_file.key.split('/')[-1]))
        # watch_file.delete()

dag = DAG('s3_dag_test', default_args=default_args, schedule_interval=timedelta(1))

t1 = BashOperator(
    task_id='bash_test',
    bash_command='echo "hello, it should work" > s3_conn_test.txt',
    dag=dag)

# sensor = S3KeySensor(
#     task_id='check_s3_for_file_in_s3',
#     bucket_key='Dataset/0110_099.png',
#     wildcard_match=True,
#     bucket_name='textractdataset',
#     s3_conn_id='my_conn_S3',
#     timeout=18*60*60,
#     poke_interval=120,
#     dag=dag)

python_task = PythonOperator(
    task_id='text_analysis_task', 
    python_callable=process_text_analysis,
    op_kwargs={'bucket': 'textract-gs', 'document': 'file-watch-dir/0110_099.png'},
    dag=dag)

# t1.set_upstream(sensor)
python_task.set_upstream(t1)

