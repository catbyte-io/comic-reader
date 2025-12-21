FROM selenium/standalone-chrome:131.0

USER root

# install Python3, pip, venv, and Xvfb
RUN apt-get update && apt-get install -y python3-pip python3-venv xvfb build-essential libffi-dev python3-dev && apt-get clean && rm -rf /var/lib/apt/lists/*

# set Python-related environment variables
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99

# Create a user
RUN useradd -ms /bin/bash cersei

# create and activate a virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# set up the working directory
WORKDIR /comic-reader/

# copy and install requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# copy the application
COPY . /comic-reader/

# ensure correct permissions for /tmp/.X11-unix to prevent Xvfb from issuing warnings
RUN mkdir -p /tmp/.X11-unix && chmod 1777 /tmp/.X11-unix

# change ownership of venv to seluser and switch users
RUN chown -R cersei:cersei /opt/venv /comic-reader
USER cersei

# run Xvfb and the Python script
CMD ["sh", "-c", "Xvfb :99 -ac & exec gunicorn --workers=4 --bind=0.0.0.0:8000 app:app"]
