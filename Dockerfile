FROM apache/airflow:2.10.5-python3.12

USER airflow
RUN pip install --no-cache-dir "apache-airflow==2.10.5" pandas openpyxl python.dotenv \
	&& python -m venv /home/airflow/dbt_venv \
	&& /home/airflow/dbt_venv/bin/pip install --no-cache-dir dbt-postgres
