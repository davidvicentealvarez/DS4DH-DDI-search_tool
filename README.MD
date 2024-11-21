# Questionnaire review tool for Disability Data & Research

## Overview

### This tool is a web service to help users find and annotate passage in files that mentions either questions about the Washington Group questions or any sort of text that mention functional difficulties and disabilities.

## Installation Guide (From GitHub)🔧

### Prerequisites:
- **Docker** and **Docker Compose** installed.
- Ensure at least **8GB of free disk space** for the database.
- A minimum of **4GB of RAM** is required for the database.

### Installation and Execution Steps:

1. **Clone**:  
   - Clone this repository in your desired directory.

2. **install ElasticSearch** 
   - Download the [ElasticSearch archive](https://www.elastic.co/downloads/past-releases#elasticsearch) that correspond to your operating system (version  8.5.0 was used)
   - Extract the files from the archive in this directory
   - Execute the file located at: 
   
      - On windows
         ```cmd
         .\elasticsearch-8.x.x\bin\elasticsearch.bat
         ```
      - On lnux and Mac:
         ```bash
         ./elasticsearch-8.x.x/bin/elasticsearch
         ```
   - Follow the instructions, it will ask you to create a password and username. Save the password, username and the signature. You will need it later
   - Change the configuration of ElasticSearch. To do this, copy the file located at `elasticsearch.yml` into the config directory of the installation of ElasticSearch in `elasticsearch-8.x.x/config`
   - Copy the newly certificates created by ElasticSearch from `elasticsearch-8.x.x/config/certs` into `src/certs`
   - Update the variables "ES_PWD" and "ES_USER" in `src/settings.py` with the newly created password and usernames from ElasticSearch
   - Reboot Elasticsearch to apply the new settings (close the terminal and re-execute the file)
   - Open a terminal and navigate to this folder.
   - Create the 2 indexes used by the tool by executing the following 2 commands :

      ```bash
      curl -X PUT "http://localhost:9800/disabilities_clean" -d @disabilities_index.json --header "Content-Type: application/json"
      ```
      This create the full text index

      ```bash
      curl -X PUT "http://localhost:9800/disabilities_chunks_clean" -d @disabilities_chunk_index.json --header "Content-Type: application/json"
      ```


3. **Build the Docker Image**: 

   Run the following command in tne same console to build the Docker image without using cached layers:  
   ```bash
   docker compose build --no-cache
   ```

4. **Run the Service**:  
   After the build is complete, start the web service by executing:  
   ```bash
   docker compose up
   ```  
   - To run the service in detached mode (background), append the `-d` flag:  
     ```bash
     docker compose up -d
     ```
    The service will be avalaible at the follwong location : `http://localhost:8901/ddi`

5. **Stopping the Service**:  
   To stop the service:  
   - Press `CTRL + C` if the service is running in the foreground (attached mode).  
   - Alternatively, use the following command to stop and remove the containers:  
     ```bash
     docker compose down
     ```

## Project File Structure 📁

```yaml
├── drive
│   └── Questionnaire_clean: The location of the saved PDF from the analysis tool. It's here you can add, 
│                            rename or delete a country by renaming or deleting its folder
├── elasticsearch-8.5.0 : The database used for this tool
├── src
│   ├── certs : HTTPS certificates needed for the database
│   ├── static 
│   │   └── media : Location of static files for the web service (icons, images, JS libraries, etc.)
│   ├── templates : HTML files of the web server
│   ├── app.py : Defines REST API endpoints and HTML web pages
│   ├── elastic_query.py : Python script for querying the database
│   ├── excel_writer.py : Python script for generating an Excel file from user annotations
│   ├── file_extractor.py : Python script for reading files, splitting them into chunks, and uploading them to the database
│   ├── settings.py : Static variables for the project
│   ├── wsgi.py : Entry point for the web service
│   ├── requirements.txt : Python libraries required for the Docker image
│   └── start_api.sh : Bash script to start the web service (using Gunicorn)
├── docker-compose.yml : Configuration for the Docker containers
├── Dockerfile : Instructions for building the Docker image
├── disabilities_chunk_index.json : Settings and mappings for the database index containing file chunks
└── disabilities_index.json : Settings and mappings for the database index containing full files as text
```