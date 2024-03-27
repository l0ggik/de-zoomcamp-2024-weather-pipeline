terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "5.6.0"
    }
  }
}

provider "google" {
  credentials = file(var.credentials)
  project     = var.project
  region      = var.region
}


resource "google_storage_bucket" "de_zoomcamp_weather_bucket" {
  name          = var.gcs_bucket_name
  location      = var.location
  force_destroy = true


  lifecycle_rule {
    condition {
      age = 1
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }
}

resource "google_storage_bucket" "de_zoomcamp_weather_temp_bucket" {
  name          = "de_2024_temp_weather_data_bucket"
  location      = var.location
  force_destroy = true
}


resource "google_storage_bucket_object" "main_python_file" {
  name   = "script/weather_pipeline.py"
  source = "../weather_pipeline.py"
  bucket = var.gcs_bucket_name
  depends_on = [ google_storage_bucket.de_zoomcamp_weather_bucket ]
}


resource "google_bigquery_dataset" "de_2024_weather_data" {
  dataset_id = var.bq_dataset_name
  location   = var.location
  delete_contents_on_destroy = true
}


data "google_service_account" "default" {
  project      = var.project
  account_id   = var.service_account_id
}

resource "google_dataproc_cluster" "weather_data_processing_cluster" {
  name   = var.dataproc_cluster_name
  region = var.dataproc_region
  project = var.project
  depends_on = [ data.google_service_account.default, google_storage_bucket_object.main_python_file ]

  cluster_config {
    master_config {
      num_instances = 1
      machine_type  = "n2-standard-4"
      disk_config {
        boot_disk_type    = "pd-ssd"
        boot_disk_size_gb = 50
      }
    }

    software_config {
      override_properties = {
        "dataproc:dataproc.allow.zero.workers": "true"
      }
    }
  
    gce_cluster_config {
      service_account = data.google_service_account.default.email
      service_account_scopes = ["cloud-platform"]
    }
  }
}

resource "google_dataproc_job" "pyspark" {
  region       = var.dataproc_region
  force_delete = true
  depends_on = [ google_dataproc_cluster.weather_data_processing_cluster ]
  placement {
    cluster_name = var.dataproc_cluster_name
  }

  pyspark_config {
    main_python_file_uri = var.main_python_file_uri
    jar_file_uris = ["gs://spark-lib/bigquery/spark-bigquery-with-dependencies_2.12-0.36.1.jar"]
    properties = {
      "spark.logConf" = "true"
    }
  }
}