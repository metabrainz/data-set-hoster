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
FROM tiangolo/uwsgi-nginx-flask:python3.8

RUN apt-get update && apt-get install -y ca-certificates

RUN mkdir /hoster
WORKDIR /hoster
COPY . /hoster
RUN python -m pip install -r requirements.txt
# Change the COPY command below to copy any config files or other 
# modules you may need (e.g. config.py) to /app:
COPY main.py config.py /app/
RUN chmod +x /app/main.py
