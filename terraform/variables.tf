variable "credentials" {
  description = "Google Cloud credentials"
  # Please set the folder where your google gloud account key file is located
  default     = "../keys/google.json"
}

variable "service_account_id" {
  description = "Service account id (the one you created for the terraform part of the zoomcamp)"
  # Please set the following variable to the id of the service account when you did the terraform module (for me it is terraform)
  default     = "terraform"
} 

variable "project" {
  description = "Project"
  # Please set this to the name of an existing Project
  default     = ""
}

variable "region" {
  description = "Region"
  #Update the below to your desired region
  default     = "europe-west10-a"
}

variable "dataproc_region" {
  description = "Region for the dataproc cluster (europe-west10-a is not allowed)"
  default     = "europe-west10"
}

variable "location" {
  description = "Project Location"
  #Update the below to your desired location
  default     = "EU"
}

variable "bq_dataset_name" {
  description = "My very unique Dataset Name"
  #Do not change!!
  default     = "de_2024_weather_data"
}

variable "gcs_bucket_name" {
  description = "Unique bucket name"
  #Do not change!!
  default     = "de_2024_weather_data_bucket"
}

variable "gcs_storage_class" {
  description = "Bucket Storage Class"
  #Do not change!!
  default     = "STANDARD"
}

variable "dataproc_cluster_name" {
  description = "Name for the dataproc cluster"
  #Do not change!!
  default = "de-weather-processing-cluster"
}

variable "main_python_file_uri" {
  description = "Uri for the main python file that will run the pipeline"
  #Do not change!!
  default = "gs://de_2024_weather_data_bucket/script/weather_pipeline.py"
}