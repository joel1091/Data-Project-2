# Data-Project-2

Dataflow: pipeline-dataflow.py es la última versión
(local)
python pipeline_dataflow.py \
--project_id <PROJECT_ID> \
--help_topic projects/<PROJECT_ID>/topics/necesitados-events \
--volunteers_topic projects/<PROJECT_ID>/topics/ayudantes-events \
--help_subscription projects/<PROJECT_ID>/subscriptions/necesitados-events-sub \
--volunteers_subscription projects/<PROJECT_ID>/subscriptions/ayudantes-events-sub \
--bigquery_dataset matched_users

Generadores: elegir los automáticos o usar streamlit para enviar mensajes manuales (streamlit se puede desplegar en local con un `streamlit run app.py` o usando cloud run 
Terraform: no debería dar problema al darle a apply
