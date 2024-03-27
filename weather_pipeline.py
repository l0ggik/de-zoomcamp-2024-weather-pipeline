import requests
import zipfile
import re
from os import listdir
from os.path import isfile, join
import subprocess
import os
from pyspark.sql import SparkSession
from pyspark.sql import types

spark = SparkSession.builder \
    .appName('weatherpipeline') \
    .getOrCreate()

spark.conf.set('temporaryGcsBucket', 'de_2024_temp_weather_data_bucket')

# this sets the correct types for the dataframe
schema = types.StructType([
    types.StructField('STATIONS_ID', types.IntegerType(), True),
    types.StructField('MESS_DATUM', types.TimestampType(), True),
    types.StructField('QN_9', types.IntegerType(), True),
    types.StructField('TT_TU', types.DecimalType(precision=5, scale=1), True),
    types.StructField('RF_TU', types.DecimalType(precision=5, scale=1), True),
    types.StructField('eor', types.StringType(), True),
])

# create folders if they do not exist, otherwise creating files would cause an error
if not os.path.isdir('./data'):
    os.mkdir('./data')
if not os.path.isdir('./data/air_temperature'):
    os.mkdir('./data/air_temperature')
if not os.path.isdir('./zips'):
    os.mkdir('./zips')

base_url = 'https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/air_temperature/recent/'
response = requests.get(base_url)
# if you open base_url in the browser you will see that its just a list of files and we need to extract the correct file names from the list with a bit of regex
filenames  = re.findall(r'(?<=href=\")stundenwerte_[A-Z\d]{1,2}_\d{5}_akt.zip(?=\">)|(?<=href=\")stundenwerte_[A-Z\d]{1,2}_\d{5}_row.zip(?=\">)', response.text)
for filename in filenames:
    # download the file
    response = requests.get(base_url + filename)
    # save file as zip
    with open(f'./zips/{filename}', 'wb') as write_zip: 
        write_zip.write(response.content)
    # open zipfile
    with zipfile.ZipFile(f'./zips/{filename}') as zip_file:
        # get a list of all files inside the zip file
        file_name_list = zip_file.namelist()
        # find the file that contains the data with the measurements
        file_name = [i for i in file_name_list if 'produkt' in i]
        # there should only be one file but in case it finds more than one file it throws a warning
        if len(file_name) > 1:
            print('Found more than one file', file_name)
        else:
            zip_file.extract(file_name[0], './data/air_temperature')
    try:
        # try to remove the zip file to prevent data being left and show a warning if file does not exist
        os.remove(f'./zips/{filename}')
    except FileNotFoundError:
        print('File not found:', filename)
# pyspark is not able to find the files on the master node of the dataproc cluster so we need to copy all extracted files to a storage bucket
# this starts the subprocess 'gsutil' which copies the files
subprocess.run(["gsutil", "-m", "cp", "-r", f'./data/air_temperature/*', f'gs://de_2024_temp_weather_data_bucket/data/air_temperature'], check=True)
datafiles_path = 'gs://de_2024_temp_weather_data_bucket/data/air_temperature'
# we need the filenames of all the files we extracted to create pyspark dataframes from them
file_names = [join(datafiles_path, filename) for filename in listdir('./data/air_temperature') if isfile(join('./data/air_temperature', filename))]
for file_name in file_names:
    # from every file we create a pyspark dataframe. We have to set some options to be able to get it working
    # we use the first line as header
    # we use ';' as delimiter
    # we have to ignore whitespaces, the files we donwloaded are txt files but we handle them as csv. The txt files are made to be human readable so they contain white spaces to create columns
    # the measurement date has a really weird timestamp format like this: 2024030408 its the date and at the end the hour of the day the measurement was done so in this case fourth of march 2024 at 8 o'clock
    df = spark.read.option('header', True).option("delimiter", ";").option('ignoreLeadingWhiteSpace', True).option('timestampFormat', "yyyyMMddHH").schema(schema).csv(file_name)
    # we can extract the station id and use it to prepartition the resulting parquet files by station id
    station_id = df.collect()[0][0]
    df = df.repartition(1)
    df.write.parquet(f'gs://de_2024_weather_data_bucket/parquet/air_temperature/{station_id}', mode='overwrite')

# after creating the data lake we want to load all parquet files into one big dataframe 
df_air = spark.read.parquet('gs://de_2024_weather_data_bucket/parquet/air_temperature/*/*')
# now we can clean the data, 'QN_9' is a information about the quality of the data and in our case can be ignored, eor means end of row and also has no use for us 
df_air = df_air.drop('QN_9', 'eor')
# sometimes measurements are missing, if the measurement is missing it is replaced with -999 in the raw data, we need to replace -999 with none because we can handle none
df_air = df_air.na.replace(-999, None)
# some renaming of columns
df_air = df_air.withColumnRenamed('STATIONS_ID', 'station_id')
df_air = df_air.withColumnRenamed('MESS_DATUM', 'date_measured')
df_air = df_air.withColumnRenamed('TT_TU', 'air_temperature')
df_air = df_air.withColumnRenamed('RF_TU', 'humidity')

# and now we write everything to bigquery
df_air.write.format('bigquery').option('table', 'de_2024_weather_data.air_temperature').option("writeMethod", "direct").save()