FROM puckel/docker-airflow:1.10.9

USER root

COPY /config/airflow.cfg ./airflow.cfg
COPY /dags ./dags

COPY /.aws ./.aws

COPY entrypoint.sh /entrypoint.sh
COPY requirements.txt /requirements.txt

# Add directory in which pip installs to PATH
ENV PATH="/usr/local/airflow/.local/bin:${PATH}"

USER airflow

ENTRYPOINT ["/entrypoint.sh"]

# Just for documentation. Expose webserver, worker and flower respectively
EXPOSE 8080
EXPOSE 8793
EXPOSE 5555
