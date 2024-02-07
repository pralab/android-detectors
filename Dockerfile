FROM python:3.9

COPY "./requirements.txt" "./"
RUN python -m pip install -r requirements.txt
WORKDIR /android-detectors
COPY "./" "./"
ENV PYTHONPATH "${PYTHONPATH}:/android-detectors/src"