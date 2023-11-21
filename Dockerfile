FROM --platform=linux/arm64 node:21.2.0 as frontend-stage

COPY ./frontend /stage/frontend
COPY package.json /stage
COPY package-lock.json /stage
COPY rollup.config.js /stage

WORKDIR /stage

RUN npm install
RUN npm run build

FROM --platform=linux/arm64 python:3.11.4 as backend-stage

ENV TZ=Asia/Seoul
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y gcc
RUN pip install --upgrade pip

COPY . /server
COPY --from=frontend-stage /stage/frontend/static/build /server/frontend/static/build
RUN pip install --no-cache-dir -r /server/requirements.txt

WORKDIR /server
CMD bash -c "gunicorn -w $(nproc) -k uvicorn.workers.UvicornWorker -b 0.0.0.0:80 app:app"

