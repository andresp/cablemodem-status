FROM python:3

WORKDIR /app

ENV TZ UTC

ADD retriever.py /app/retriever.py
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN pip install requests beautifulsoup4 lxml influxdb schedule python-logging-loki

CMD ["retriever.py"]
ENTRYPOINT ["python3"]