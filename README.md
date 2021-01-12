# Cable Modem status retriever

This script retrieves channel information from a cable modem and stores time series data to an InfluxDB. The data can then be visualized using tools such as Grafana.

## Supported Modems

* Netgear CM2000

## Dependencies

* Python3
* An InfluxDB database

## Installation

Install the following packages with pip

`pip3 install requests beautifulsoup4 influxdb`

## Configuration

Edit [configuration.ini](./configuration.ini) and fill in your information for the InfluxDB and the modem.

## Executing the script

Test the script by executing it manually and verify it completes without error messages.

`python3 retriever.py`

## Set up recurring execution

Create a cron job (executes every 2 minutes):

`*/2 * * * * /usr/bin/python3 /opt/cm-status/retriever.py 2>&1 > /dev/null`

## Todo

* Make the script modular to support various types of modems. Priority on latest gen DOCSIS 3.1 modems such as:
  * Arris S33
  * Arris SB8200
  * Motorola MB8600
* Support collecting event log items
* Provide a Grafana Dashboard to visualize collected data
* Provide turnkey instructions to set up InfluxDB, Grafana and retrieval script
* Consider providing a containerized application