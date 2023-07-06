#!/bin/bash

# .env 파일의 존재 확인
if [ ! -f "./test/.env" ]; then
    echo "오류: ./test 디렉토리에 .env 파일이 존재하지 않습니다."
    exit 1
fi

# Docker 이미지 빌드
docker build . -t econox

# Docker 컨테이너를 환경변수와 함께 실행
docker run --env-file ./test/.env -p 80:80 econox
