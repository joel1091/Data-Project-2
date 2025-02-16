### Esto se hará en terraform, para ejecutarlo manualmente:

docker build -t gcr.io/<PROJECT_ID>/custom-grafana .
docker push gcr.io/<PROJECT_ID>>/custom-grafana

### Deploy cloud run (manual)
gcloud run deploy grafana --image gcr.io/<PROJECT_UD>/custom-grafana --platform managed --service-account <SERVICE_ACCOUNT> --port 3000 --memory 1Gi

# Una vez en Grafana:
Connections > Add new connection
Search Google BigQuery
Install and add new data source
GCE Default Service Account > "project_id"
Go to dashboards
Click on new and import
Import dashboard-grafana.json
Select a Google BigQuery data source (default is the one you just created)