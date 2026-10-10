from __future__ import annotations

from datetime import timedelta

import pendulum
from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator

DBT = "/home/airflow/dbt_venv/bin/dbt"
DBT_PROJ = "--project-dir /opt/airflow/dbt --profiles-dir /opt/airflow/dbt"
# target/log paths go to /tmp so dbt doesn't write into the mounted repo
DBT_ARGS = (
        f"{DBT_PROJ} "
        "--target-path /tmp/dbt_target --log-path /tmp/dbt_logs"
        )

@dag(
        dag_id="housing_pipeline",
        schedule="@weekly",
        start_date=pendulum.datetime(2026, 1, 1, tz="Europe/Madrid"),
        catchup=False,
        default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
        tags=["housing"],
        )

def housing_pipeline():
    @task
    def extract_ine():
        from extract.ine import main

        main()

    @task
    def extract_serpavi():
        from extract.serpavi import main

        main()

    @task
    def load_raw():
        from load.load_raw import main

        main()

    @task
    def export_mart():
        from export.export_mart import main

        main()

    dbt_deps = BashOperator(task_id="dbt_deps", bash_command=f"{DBT} deps {DBT_PROJ}")
    dbt_build = BashOperator(task_id="dbt_build", bash_command=f"{DBT} build {DBT_ARGS}")

    [extract_ine(), extract_serpavi()] >> load_raw() >> dbt_build >> export_mart()

housing_pipeline()
