FROM node:21.2.0 as frontend-stage

COPY ./frontend /stage/frontend
COPY package.json /stage
COPY package-lock.json /stage
COPY rollup.config.js /stage

WORKDIR /stage

RUN npm install
RUN npm run build

FROM python:3.11.6 as backend-stage

ENV TZ=Asia/Seoul
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y gcc
RUN pip install --upgrade pip

COPY . /server
COPY --from=frontend-stage /stage/frontend/static/build /server/frontend/static/build
RUN pip install -r /server/requirements.txt

WORKDIR /server
CMD uvicorn app:app --host 0.0.0.0 --port 80