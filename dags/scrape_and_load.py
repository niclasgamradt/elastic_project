from pathlib import Path
import sys

# Projekt-Root ermitteln: .../elastic_project
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

from scripts.apply_es import main as apply_es_main
from scripts.fetch_raw import main as fetch_raw_main
from scripts.preprocess import main as preprocess_main
from scripts.load_to_es import main as load_to_es_main
from scripts.post_checks import main as post_checks_main





with DAG(
    dag_id="scrape_and_load",
    start_date=datetime(2025, 12, 1),
    schedule="@daily",      # später: @hourly oder cron
    catchup=False,
    tags=["elastic_project"],
) as dag:

    apply_es = PythonOperator(
        task_id="apply_es",
        python_callable=apply_es_main,
    )

    fetch_raw = PythonOperator(
        task_id="fetch_raw",
        python_callable=fetch_raw_main,
    )

    preprocess = PythonOperator(
        task_id="preprocess",
        python_callable=preprocess_main,
    )

    load_to_es = PythonOperator(
        task_id="load_to_es",
        python_callable=load_to_es_main,
    )

    post_checks = PythonOperator(
        task_id="post_checks",
        python_callable=post_checks_main,
    )

    apply_es >> fetch_raw >> preprocess >> load_to_es >> post_checks
