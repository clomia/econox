#!/bin/bash

# .env 파일의 존재 확인
if [ ! -f "./test/.env" ]; then
    echo "오류: ./test 디렉토리에 .env 파일이 존재하지 않습니다."
    exit 1
fi

# .env 파일에서 환경변수 읽어오기
set -a
source ./test/.env
set +a

npm run build # svelte 코드 빌드 & 번들링

# 종료 처리기 함수
cleanup() {
  # pycache 파일 제거
  find . | grep -E "(/__pycache__$|\.pyc$|\.pyo$)" | xargs rm -rf
  # 빌드된 번들링 파일 제거
  rm -rf frontend/static/build
  echo "종료 작업 완료: pycache 관련 파일들과 번들링된 JavaScript 파일들을 정리하였습니다."
}

# 종료 시그널을 받으면 cleanup 함수 실행
trap cleanup EXIT

# FastAPI 서버 실행
uvicorn app:app --reload