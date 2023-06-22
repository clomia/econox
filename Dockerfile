FROM python:3.11.4

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y gcc
RUN pip install --upgrade pip

COPY . /server
RUN pip install --no-cache-dir -r /server/requirements.txt

WORKDIR /server
CMD bash -c "gunicorn -w $(nproc) -k uvicorn.workers.UvicornWorker -b 0.0.0.0:80 app:app"

