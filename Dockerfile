FROM python:3.9

COPY "./requirements.txt" "./"
RUN python -m pip install -r requirements.txt
WORKDIR /
COPY "./" "./android-detectors"
ENV PYTHONPATH "${PYTHONPATH}:/android-detectors/src"
