FROM python:3.13

WORKDIR /backend

COPY . /backend

RUN apt update
RUN apt install ffmpeg -y
RUN pip install -r requirements.txt
RUN poetry install

CMD [ "/bin/bash", "./entry.sh" ]
