# See documentation:
# docs/06_ingestion_pipeline.md

from pathlib import Path
import sys
from datetime import datetime, timedelta

# Projekt-Root ermitteln: .../elastic_project
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from airflow import DAG
from airflow.operators.python import PythonOperator

from scripts.apply_es import main as apply_es_main

# Klar benannte Callables (keine Namenskollision mit Tasks)
from scripts.fetch_brightsky import main as fetch_brightsky_main
from scripts.preprocess_brightsky import main as preprocess_brightsky_main

from scripts.fetch_hs_wetter import main as fetch_hs_main
from scripts.preprocess_hs_wetter import main as preprocess_hs_main

from scripts.load_to_es import main as load_to_es_main
from scripts.post_checks import main as post_checks_main


with DAG(
    dag_id="scrape_and_load",
    start_date=datetime(2025, 12, 1),
    schedule="@daily",
    catchup=False,
    tags=["elastic_project"],
    default_args={
        "retries": 5,
        "retry_delay": timedelta(minutes=5),
    },
) as dag:

    apply_es = PythonOperator(
        task_id="apply_es",
        python_callable=apply_es_main,
    )

    fetch_brightsky = PythonOperator(
        task_id="fetch_brightsky",
        python_callable=fetch_brightsky_main,
        op_kwargs={"run_id": "{{ ds }}"},
    )

    preprocess_brightsky = PythonOperator(
        task_id="preprocess_brightsky",
        python_callable=preprocess_brightsky_main,
        op_kwargs={"run_id": "{{ ds }}"},
    )

    fetch_hs = PythonOperator(
        task_id="fetch_hs",
        python_callable=fetch_hs_main,
        op_kwargs={"run_id": "{{ ds }}"},
    )

    preprocess_hs = PythonOperator(
        task_id="preprocess_hs",
        python_callable=preprocess_hs_main,
        op_kwargs={"run_id": "{{ ds }}"},
    )

    load_to_es = PythonOperator(
        task_id="load_to_es",
        python_callable=load_to_es_main,
        op_kwargs={"run_id": "{{ ds }}"},
    )

    post_checks = PythonOperator(
        task_id="post_checks",
        python_callable=post_checks_main,
    )

    # Ablauf: erst ES konfigurieren, dann beide Quellen, dann laden, dann Checks
    apply_es >> fetch_brightsky >> preprocess_brightsky
    apply_es >> fetch_hs >> preprocess_hs

    [preprocess_brightsky, preprocess_hs] >> load_to_es >> post_checks
