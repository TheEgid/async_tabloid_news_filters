FROM python:3.8

RUN apt-get update && apt-get install -qy apt-utils
	
ENV PYTHONUNBUFFERED 1

WORKDIR /opt

RUN pip3 install --upgrade pip

COPY ./requirements.txt /opt

RUN pip install -r requirements.txt

COPY . /opt

EXPOSE 80

CMD ["python3", "main.py", "-host", "0.0.0.0", "-port", "5000", "-redis_host", "redis", "-redis_port", "6379", "-use_cache"]
