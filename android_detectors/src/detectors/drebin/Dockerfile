FROM python:3.10

WORKDIR /app
COPY ./requirements.txt /app
RUN pip install -r ./requirements.txt
COPY ./src/detectors/drebin/requirements.txt /app
RUN pip install -r ./requirements.txt

COPY . /app