import json
import pathlib

#import airflow.utils.dates
import requests
import requests.exceptions as requests_exceptions
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime

dag = DAG(
    dag_id="aa_tp8",
    description="Download rocket pictures of recently launched rockets.",
    start_date=datetime(2024, 4, 18),
    schedule_interval="@daily",
)

download_launches = BashOperator(
    task_id="download_launches",
    bash_command="curl -o /tmp/launches.json -Lk 'https://ll.thespacedevs.com/2.0.0/launch/upcoming'",  # noqa: E501
    dag=dag,
)


def _get_pictures():
    # Ensure directory exists
    pathlib.Path("/tmp/images").mkdir(parents=True, exist_ok=True)

    # Download all pictures in launches.json
    with open("/tmp/launches.json") as f:
        launches = json.load(f)
        image_urls = [launch["image"] for launch in launches["results"]]
        for image_url in image_urls:
            try:
                response = requests.get(image_url)#envoyer une requête HTTP GET à l'URL de l'image spécifiée par la variable "image_url" et stocker la réponse dans la variable "response".
                image_filename = image_url.split("/")[-1]#-1 est l'indice du dernier élément.
                target_file = f"/tmp/images/{image_filename}"
                with open(target_file, "wb") as f:
                    f.write(response.content)
                print(f"Downloaded {image_url} to {target_file}")
            except requests_exceptions.MissingSchema:
                print(f"{image_url} appears to be an invalid URL.")
            except requests_exceptions.ConnectionError:
                print(f"Could not connect to {image_url}.")


get_pictures = PythonOperator(
    task_id="get_pictures", python_callable=_get_pictures, dag=dag
)

notify = BashOperator(
    task_id="notify",
    bash_command='echo "There are now $(ls /tmp/images/ | wc -l) images."',
    dag=dag,
)

download_launches >> get_pictures >> notify

