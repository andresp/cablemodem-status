# Cable Modem Status Retriever

This script retrieves channel information from a cable modem and stores time series data to an InfluxDB as well as Event Logs in Loki. The data can be visualized using tools such as Grafana.

## Supported Modems

* Netgear CM2000

## Dependencies

* Python3
* An InfluxDB database
* Loki for Event Log collection

## Installation

Install the following packages with pip

`pip3 install requests beautifulsoup4 influxdb schedule`

Optionally, for log collection:

`pip3 install python-logging-loki`

## Configuration

Edit [configuration.ini](./configuration.ini) and fill in your information for the InfluxDB and the modem.

## Executing the script

Test the script by executing it manually and verify it completes without error messages.

`python3 retriever.py`

## Set up recurring execution

Create a cron job (executes every 2 minutes):

`*/2 * * * * /usr/bin/python3 /opt/cm-status/retriever.py 2>&1 > /dev/null`

## Docker

You can build your own image by running:

`docker build -f "Dockerfile" -t cablemodemstatus:latest .`

Once built, create a directory on your host for your configuration.ini file, such as `/opt/cablemodemstatus`. Then start a container referring to the configuration directory and mapping it to `/app/data`:

`docker run -d --name cablemodemstatus --restart unless-stopped -v /opt/cablemodemstatus:/app/data cablemodemstatus:latest`

You can monitor the container's status by running:

`docker logs -f cablemodemstatus`

## Todo

* Make the script modular to support various types of modems. Priority on latest gen DOCSIS 3.1 modems such as:
  * Arris S33
  * Arris SB8200
  * Motorola MB8600
* Provide a Grafana Dashboard to visualize collected data
* Provide turnkey instructions to set up InfluxDB, Grafana and retrieval script