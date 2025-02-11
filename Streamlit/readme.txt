# Como desplegarlo:

## Ejecutar el siguiente código para crear la imagen (del dockerfile)
gcloud builds submit --tag gcr.io/<id_project>/streamlit-app


## Para el cloudrun (para acceder a la app con un link)
gcloud run deploy app `
  --image gcr.io/<id_project>/streamlit-app `
  --platform managed `
  --region europe-west1 `
  --allow-unauthenticated `
  --port 8501
