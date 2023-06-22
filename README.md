## ECONOX  
### 프로젝트 구조
- FastAPI를 사용하여 백엔드를 개발합니다. 
	- Entry point는 main.py입니다.
	- 모든 리소스를 FastAPI에 통합해서 main.py로 모두 실행합니다.
- Jinja2를 사용하여 프론트엔드를 개발합니다.
	- templates/ 에 템플릿을 작성합니다. (통신 부분)
	- CSS, JS는 static/ 디렉토리에 작성합니다. (로직 부분)
	- 데이터 시각화는 Apache ECharts를 사용합니다.
- 외부 API를 사용해서 데이터를 수집합니다.
	- fmp/ 는 Financial Modeling Prep API 를 추상화합니다.
	- 기타 다른 API도 fmp/ 처럼 패키지로 격리, 추상화하여 사용합니다.
- 고성능 데이터 처리는 Numpy기반으로 xarray , zarr , numba등을 통해 수행합니다.
	- compute/ 에 데이터 연산 로직을 격리, 추상화합니다.
- 데이터 저장은 파일 시스템과 DB를 사용합니다.
	- 운영에 필요한 비즈니스 데이터는 DB(PostgreSQL)를 사용합니다.
	- 기능에 필요한 핵심 데이터는 File(xarray + zarr)을 사용합니다.
### Git 컨벤션
- 브랜치는 main, staging, dev 로 나누어 관리합니다.
	- main: 운영 브랜치
	- staging: 안정화 브랜치
	- dev: 개발 브랜치
- dev에서 개발하고 문제없이 작동하는 업데이트 사항을 staging으로 올립니다. 모인 업데이트 내용들은 신규 버전으로 묶어서 main브랜치로 올립니다.
### 운영 전략
- 모든 개발, 테스트는 로컬에서 수행합니다.
- main push에 대한 인프라 배포 파이프라인은 추후 고려