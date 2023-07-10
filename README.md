## ECONOX  
[![builder deploy](https://github.com/clomia-group/econox/actions/workflows/deploy.yaml/badge.svg)](https://github.com/clomia-group/econox/actions/workflows/deploy.yaml)  
--> [econox.io](https://www.econox.io/)
### 프로젝트 구조
- FastAPI를 사용하여 백엔드를 개발합니다. 
	- Entry point는 app.py입니다.
	- 모든 리소스를 FastAPI에 통합해서 main.py로 모두 실행합니다.
- Svelte를 사용하여 SPA 아키텍쳐로 프론트엔드를 개발합니다.
	- 데이터 시각화는 Apache ECharts를 사용합니다.
	- 추후 Svelte Native를 사용해서 모바일 어플 개발도 가능합니다.
	- TypeScript 씁니다.
- 외부 API를 사용해서 데이터를 수집합니다.
	- fmp/ 는 Financial Modeling Prep API 를 추상화합니다.
	- world_bank/ 는 World Bank API 를 추상화합니다.
- 고성능 데이터 처리는 Numpy기반으로 xarray , zarr , numba등을 통해 수행합니다.
	- compute/ 에 데이터 연산 로직을 격리, 추상화합니다.
- 데이터 저장은 파일 시스템과 DB를 사용합니다.
	- 운영에 필요한 비즈니스 데이터는 DB(PostgreSQL)를 사용합니다.
	- 기능에 필요한 핵심 데이터는 File(xarray + zarr , json ...)을 사용합니다.
### Git 컨벤션
- 브랜치는 main, staging, dev 로 나누어 관리합니다.
	- prod: 운영 브랜치
	- staging: 안정화 브랜치
	- dev: 개발 브랜치
- dev에서 개발하고 문제없이 작동하는 업데이트 사항을 staging으로 올립니다. 모인 업데이트 내용들은 신규 버전으로 묶어서 main브랜치로 올립니다.
