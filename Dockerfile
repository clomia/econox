FROM node:18.16.1 as frontend-stage

COPY ./frontend /stage/frontend
COPY package.json /stage
COPY rollup.config.js /stage

WORKDIR /stage

RUN npm install
RUN npm run build

FROM python:3.11.4 as backend-stage

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y gcc
RUN pip install --upgrade pip

COPY . /server
COPY --from=frontend-stage /stage/frontend/static/build /server/frontend/static/build
RUN pip install --no-cache-dir -r /server/requirements.txt

WORKDIR /server
CMD bash -c "gunicorn -w $(nproc) -k uvicorn.workers.UvicornWorker -b 0.0.0.0:80 app:app"

