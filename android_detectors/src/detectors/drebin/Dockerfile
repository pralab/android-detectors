# This is customizable...
FROM python:3.10

# The next steps must be always followed----------------------------------
WORKDIR /app
COPY ./requirements.txt /app
RUN pip install -r ./requirements.txt
# -----------------------------------------------------------------------------

# Instead of copying the entire project directory `.`, I first copy the
#  requirements only and install them...
COPY ./src/detectors/drebin/requirements.txt /app
RUN pip install -r ./requirements.txt

# Now I copy the entire directory. Why? Because if I need to modify something
#  in the code, it will alter the image building only from this point.
#  Instead, for the previous (longer) steps Docker will use the cache.
COPY . /app
