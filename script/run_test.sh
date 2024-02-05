#!/bin/bash

# ---- 테스트를 위한 Python 모듈 실행 ---
# 사용 예시: sh script/run_test backend/data/text/method.py
#   - method 모듈을 실행시켜보고 싶은 경우 위와 같이 하면 됩니다.

# 서버는 이 환경변수 유/무로 로컬 여부를 확인함
export IS_LOCAL="true"

# Redis 서버 시작
redis-server &

# 종료 처리기 함수
cleanup() {
  
  pid=$(ps aux | grep redis-server | grep -v grep | awk '{print $2}')
  # Redis 서버 종료 (이렇게 안해도 ctrl+c로 인해 종료되는듯 하나, 안전빵)
  if [ ! -z "$pid" ]; then
      echo "Redis 서버 종료 중 (PID: $pid)"
      kill $pid
      echo "Redis 서버가 종료되었습니다."
  else
    echo "실행 중인 Redis 서버가 없습니다."
  fi

  # pycache 파일 제거
  find . | grep -E "(/__pycache__$|\.pyc$|\.pyo$)" | xargs rm -rf

  echo "종료 작업 완료: Redis 서버를 종료하고 pycache 관련 파일들을 정리하였습니다."
}

# 종료 시그널을 받으면 cleanup 함수 실행
trap cleanup EXIT

# EFS 볼륨 역할을 대신할 디렉토리 생성
mkdir -p efs-volume

python $1 # 커멘드로 입력된 python 모듈 실행
