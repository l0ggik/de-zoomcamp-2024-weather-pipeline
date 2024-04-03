# Data Engineering Zoomcamp Project

## Problem statement

For my project i decided to process weather data supplied by the DWD (Deutscher Wetterdienst - German Meteorological Service). The DWD is basically responsible for collecting the weather data for Germany. The weather data is aggregated and can be downloaded.  
There are different time intervals for the weather measurements, for example there is data for measurements every 5 minutes, every hour of every 24 hours.  
I decided to use the hourly measurements.   
There are also different measurements like temperature, air humidity, wind speed, rain...  
Too keep the scope of the project limited, i decided to only use the data on air temperature and humidity.  
The DWD provides two kinds of data: Recent and older measurements. The recent measurements are from the last 1 1/2 years, the older data is obvisly older and goes back to the beginng of measurements. Because of project limits i also only process the recent data.  
The data can be downloaded as zip-files, these zip-files contain the measurements and some other files with explanations.  
At the moment the data is completely useless because all the data is stored in txt files that are inside a zip file. My goal for this project is to insert all the data into a database so it is possible to easyly acess all this interesting weather data ad build a dashboard out of it.  
In the long term i want to learn some data science and build an ai that can predict the weather but that is not part of this project.

## Data Pipeline

I created a batch pipeline because the weather data gets actualysed every day so processing the data once a day will be enough.
The pipeline runs completely in the cloud, after setting the correct configuration you just have to run terraform apply and everything works on its own.

## Requirements

To run the pipeline you need to have terraform and docker installed. You also need a google cloud account with some credit left (5€ or $ should be enought) and the google cloud key file you created for the terraform part of week 1.  
With terraform you can setup the complete pipeline in google cloud.  
Docker is needed because i use Grafana for the visualization of the data. This would also be possible to run in google cloud but is too much work to setup just for the project so this will run locally with the data coming from bigquery.    
If you have done week 1 of the zoomcamp you should already have this installed  
if you have not used google dataproc in your project or for the zoomcamp, you need to activate the dataproc api (search for dataproc in the cloud console and it should ask if you want to activate the API) and also give the service key you used for the terraform part the roles dataproc-admin and compute-admin (in the google cloud console under iam)  
[this video from the course might help a little bit](https://www.youtube.com/watch?v=osAiAYahvh8&list=PL3MmuxUbc_hJed7dXYoJw8DoCuVHhGEQb&index=66)  


## Steps for setting up

There are some configuration steps before you can run the pipeline. Here is what you have to do:

+ inside the projet folder, go to the terraform folder and open variables.tf  
    Set the following variables:  
    + credentials
    + service_account_id
    + project
    + region (optional, default would be europe put you can change it)
    + dataproc_region (optional, if you change the region please also change this so it fits to the region)
    + location (optional, please also change if you changed the region)  
+ if you setup everything correctly you can now initialize terraform by running `terraform init` in the terminal
this is the only part where i can't really help with. So what could happen is that terraform complains if you do the next point, try to google the error in case you get stuck (the only error that might occur is that your google cloud service key does not have all the permissions needed)  
+ after terraform is initialized you can run `terraform apply` and confirming with yes when asked but you should know how terraform works  
    This will create a google dataproc cluster and run weather_pipeline.py as a pyspark job  
    Because the pipeline needs to download a lot of zip files, unzip all the files and copy all the unziped files to google storage bucked this takes quite a while to run (about 20-30 minutes) so please be patient.  
    You can whatch the job in google cloud if you want to (search for dataproc in the cloud console). In the end you should have some weather data in bigquery.   
+ to start Grafana, go to the grafana folder inside the project folder
    + run `docker compose up -d` to start the Grafana Server, the server runs on port 3002, if port 3002 is already in use please change the port in the docker-compose.yml
    + when the container is running you can open localhost:3002 in your browser and you should have the login screen for Grafana. The credentials are `admin` `admin`
    + after you have sucessfully logged in you get to the main page where you have to setup the connection to bigquery. There should be a "create connection" button, after you clicked the button there should be a collection of possible connection types. Search for bigquery and select it. This should open the create connection dialog. (you may need to click on create datasource but you should be able to find out yourself how to create a datasource). The dialog asks for a Authentication method, you can leave it set to Google JWT File. Drag and drop your key file or open a file browser to choose the correct key file. In Additional settings please set the region to the region in the variables.tf (default would be EU). This should be it, now you can test and safe the data source.
    + after setting the data source you have to create a new dashboard
        + click on create new dashboard
        + you will be asked how to create the new dashboard, please select Import a dashboard
        + Drag and drop the Weather-Dashboard.json file, which is inside the grafana folder, on the Upload dashboard JSON file field. This should create the dashboard
        you can now see the humidity and air temperature for different weather stations, (you may have to wait until the pipeline finishes, if the dashboard shows no data please make sure the pipeline finishes and there is data in bigquery) 

## Some words before the end

As this project has a very limited time frame, not everything that is possible made it into the project. For example the dashboard lists Stations with station ID, there is also data on the names and geolocations of the stations. Unfortunately this data is safed in a txt file where the columns are separated by whitespaces. Getting the station names was too much work to finish it in time. I would also liked to create a geomap for the stations so you could click on a location and see the corresponding data.
Why Grafana?
I only used google cloud because running the pipeline in the cloud was a requirement for the project. I want to use Grafana for work and this was a chance for me to try it and learn how to use Grafana.


## After you have finished evaluation

When you are finished with evaluating my project and want to delete everything do the following:  
+ in the grafana folder run `docker compose down`
+ in the terraform folder run `terraform destroy`
+ the dataproc cluster that runs the pipeline creates two temporary google storage buckets which are not destroyed automaticly, you can delete them from your google cloud account
+ in the end you can then delete the complete project folder (if you are on linux you might need root rights because the grafana docker image creates a folder as root)