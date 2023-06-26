# How to use docker to host your data set with nginx/uwsgi/flask
#---------------------------------------------------------------
# 
# Create a requirements.txt file, if you don't already have one and add this line:
# 
#   -e git+https://github.com/mayhem/data-set-hoster.git#egg=datasethoster
# 
# When the docker image is built, it will install everything listed in requirements.txt.
# 
# Then create your query object and save it to a file called main.py. Finally,
# if your script is dependent on other files, you will need to copy them into /app.
# See the comment below:
FROM tiangolo/uwsgi-nginx-flask:python3.11

RUN apt-get update && apt-get install -y ca-certificates

COPY requirements.txt /app
RUN python -m pip install -r requirements.txt

COPY datasethoster /app/datasethoster

# Change the COPY command below to copy any config files or other
# modules you may need (e.g. config.py) to /app:
COPY example/example.py example/main.py example/config.py example/uwsgi.ini /app/

ENV FLASK_ENV=development
