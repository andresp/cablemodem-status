# Cable Modem Status Retriever

This script retrieves channel information from a cable modem and stores time series data to an InfluxDB as well as Event Logs in Loki. The data can be visualized using tools such as Grafana.

## Supported Modems

* Motorola MB8600
* Netgear CM2000
* Technicolor XB7
* Arris International Touchstone TG3492, configured as Giga Connect Box for UPC.CH Switzerland

## Dependencies

* Python3
* An InfluxDB 2.0 database
* Loki for Event Log collection

## Installation

Build and install with pip

`pip3 install -e .`

## Configuration

Edit [configuration.ini](./configuration.ini) and fill in your information for the InfluxDB and the modem.

Valid strings for `ModemType`:

* `MotorolaMB8600`
* `NetgearCM2000`
* `TechnicolorXB7`
* `TouchstoneTG3492UPCCH`

## Executing the script

Test the script by executing it manually and verify it completes without error messages.

`retriever`

## Development / Contributing

Install all dev dependencies: `pip install .[dev]` .

Run unittests: `pytest tests`

## Set up recurring execution

Create a cron job (executes every 2 minutes):

`*/2 * * * * /usr/local/bin/retriever 2>&1 > /dev/null`

## Docker

You can build your own image by running:

`docker build -f "Dockerfile" -t cablemodemstatus:latest .`

Once built, create a directory on your host for your configuration.ini file, such as `/opt/cablemodemstatus`. Then start a container referring to the configuration directory and mapping it to `/app/data`:

`docker run -d --name cablemodemstatus --restart unless-stopped -v /opt/cablemodemstatus:/app/data cablemodemstatus:latest`

You can monitor the container's status by running:

`docker logs -f cablemodemstatus`

## Docker compose

If you are using Docker Compose, building and installation is even easier. 

Assuming your configuration file is 

`/home/pi/config/configuration.ini`

then all you need to add to your compose.yaml file is this:

```
  cablemodem_exporter:
     build: https://github.com/andresp/cablemodem-status.git
     command: retriever
     volumes:
       - /home/pi/config:/app/data:ro
```

## Todo

* Implement modules for additional modems:
  * Arris S33
  * Arris SB8200
* Provide a Grafana Dashboard to visualize collected data
* Provide turnkey instructions to set up InfluxDB, Grafana and retrieval script
