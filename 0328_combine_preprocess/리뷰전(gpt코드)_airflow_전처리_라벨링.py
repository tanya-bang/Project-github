from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

default_args = {
    'owner': 'project_user',
    'start_date': datetime(2024, 3, 1),
    'retries': 1
}

with DAG(
    dag_id='stock_preprocess_labeling_dag',
    default_args=default_args,
    schedule_interval=None,
    catchup=False
) as dag:

    stocks = ['samsung', 'apple', 'nvidia', 'skhynix']

    for stock in stocks:
        preprocess = BashOperator(
            task_id=f'preprocess_{stock}',
            bash_command=f'python _1_preprocess/preprocess_{stock}.py'
        )

        labeling = BashOperator(
            task_id=f'labeling_{stock}',
            bash_command=f'python _3_labeling/labeling_{stock}.py'
        )

        preprocess >> labeling
