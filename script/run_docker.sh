#!/bin/bash
# ---- Docker로 서버 실행 ---

# 사용자 입력을 통해 환경 변수 값 얻기
read -p "AWS_ACCESS_KEY_ID: " AWS_ACCESS_KEY_ID
read -p "AWS_SECRET_ACCESS_KEY: " AWS_SECRET_ACCESS_KEY

# Docker 이미지 빌드
docker build . -t econox

# Docker 컨테이너를 환경변수와 함께 실행
docker run \
    -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
    -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
    -e AWS_DEFAULT_REGION=us-east-1\
    -p 80:80 econox
