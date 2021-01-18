FROM python:3

WORKDIR /app

ADD retriever.py /app/retriever.py
RUN pip install requests beautifulsoup4 lxml influxdb schedule python-logging-loki

CMD ["retriever.py"]
ENTRYPOINT ["python3"]