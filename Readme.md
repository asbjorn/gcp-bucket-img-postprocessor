# mLINK Image postprocessor


## Steps

Assuming you already have installed Google Cloud SDK locally (and the gcloud available in your shell).
*Also* install the `gsutil` tool - a *must have* when working with GCP Storage Buckets.


```bash
export PROJECT_ID="my-project"
# get "project number" from this list
gcloud projects list
export PROJECT_NUMBER="101010101"
```
1. `gcloud config set project $PROJECT_ID`
2. `gcloud config set run/region europe-west1`


### Step 3. Create a Storage Bucket

- Create bucket where you upload images to.. `gsutil mb gs://my-example-storage-bucket`

- Create bucket where service should upload optimized images to.. `gsutil mb gs://my-example-storage-bucket-upload`


### Step 4: Create Pub/Sub topics

- one for the images: `images-to-process`
- one for those images that failed: `images-failed`

```bash
gcloud pubsub topics create images-to-process
gcloud pubsub topics create images-failed
```


### Step 4: Setup your bucket to sendt to Pub/Sub topics

```bash
gsutil notification create -f json -t images-to-process -e OBJECT_FINALIZE gs://my-example-storage-bucket
# list the notification config like this
gsutil notification list gs://my-example-storage-bucket
```


### Step 5: Build and deploy service to GCP Cloud Run

```bash
# let's just give the container the name 'pubsub'
gcloud builds submit --tag gcr.io/my-project/pubsub

# 'pubsub' is the container name, 'pubsub-tutorial' is the name of the service
# Notice the two important environment variables
gcloud run deploy pubsub-tutorial --image gcr.io/my-project/pubsub \
    --set-env-vars CLOUD_STORAGE_BUCKET=my-example-storage-bucket,CLOUD_UPLOAD_STORAGE_BUCKET=my-example-storage-bucket-upload
```

**Important:** The previous command will display the service URL. That URL is used to configure the Pub/Sub subscription

```
### Step 6: Integrate with Pub/Sub

Alrite.. We have deployed our Cloud Run service

```bash
# Enable your project to create Pub/Sub authentication tokens
gcloud projects add-iam-policy-binding ${PROJECT_-_ID} \
     --member=serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-pubsub.iam.gserviceaccount.com \
     --role=roles/iam.serviceAccountTokenCreator
```


```bash
# Create or select a service account to represent the Pub/Sub subscription identity
gcloud iam service-accounts create cloud-run-pubsub-invoker \
     --display-name "Cloud Run Pub/Sub Invoker"
```

Give the invoker service account permission to invoke your Cloud Run service "pubsub-tutorial"
```bash
gcloud run services add-iam-policy-binding pubsub-tutorial \
   --member=serviceAccount:cloud-run-pubsub-invoker@${PROJECT_ID}.iam.gserviceaccount.com \
   --role=roles/run.invoker
```

Create a Pub/Sub subscription with the service account for the Cloud Run service
```bash
gcloudpubsub subscriptions create images-to-process-subscription --topic images-to-process \
   --push-endpoint=SERVICE-URL/ \
   --push-auth-service-account=cloud-run-pubsub-invoker@${PROJECT_ID}.iam.gserviceaccount.com
```


### Step 7: Let's test with a simple message?

Send a Pub/Sub message to the topic:

```bash
gcloud pubsub topics publish images-to-process --message "Testmessage from my laptop"
```

Now check your logs: https://console.cloud.google.com/run/detail/europe-west1/pubsub-tutorial/metrics?authuser=0&project=my-project


### Step 8: Let's test by upload an image to your bucket

```bash
# Find a large image you want to test with.
# A tip is to use one from your cellphone which is usually pretty large..
gsutil cp original.jpg  gs://my-example-storage-bucket/original.jpg
```

Now go to your logs and have a look: https://console.cloud.google.com/run/detail/europe-west1/pubsub-tutorial/metrics?authuser=0&project=my-project

And *also* check the target bucket: https://console.cloud.google.com/storage/browser/my-example-storage-bucket-upload?authuser=0&project=my-project
