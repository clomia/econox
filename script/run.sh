#!/bin/bash
# ---- 로컬에서 서버 실행 ---

# 서버는 이 환경변수 유/무로 로컬 여부를 확인함
export IS_LOCAL="true"

# Redis 서버 시작
redis-server &

# Svelte 코드 빌드 & 번들링
npm run build

# 종료 처리기 함수
cleanup() {
  # Redis 서버 종료

  # pycache 파일 제거
  find . | grep -E "(/__pycache__$|\.pyc$|\.pyo$)" | xargs rm -rf

  # 빌드된 번들링 파일 제거
  rm -rf frontend/static/build

  echo "종료 작업 완료: Redis 서버를 종료하고 pycache 관련 파일들과 번들링된 JavaScript 파일들을 정리하였습니다."
}

# 종료 시그널을 받으면 cleanup 함수 실행
trap cleanup EXIT

# EFS 볼륨 역할을 대신할 디렉토리 생성
mkdir -p efs-volume

# FastAPI 서버 실행
uvicorn app:app --reload
