<img src="./frontend/static/img/logo.png" alt="logo" width="200"/>  

[![builder deploy](https://github.com/clomia-group/econox/actions/workflows/deploy.yaml/badge.svg)](https://github.com/clomia-group/econox/actions/workflows/deploy.yaml)  
[![wakatime](https://wakatime.com/badge/user/eaedfb05-2b60-4cd6-8436-6a673d9bd06f/project/c7596db5-6e65-494d-80d7-462ce4dc9aa4.svg)](https://wakatime.com/badge/user/eaedfb05-2b60-4cd6-8436-6a673d9bd06f/project/c7596db5-6e65-494d-80d7-462ce4dc9aa4)
# [econox.io](https://www.econox.io/)  
[**UI 디자인 스케치**](https://assets.adobe.com/id/urn:aaid:sc:AP:01ecd7d2-71fb-4581-ba0f-c692b42eeba5?view=published)
## 프로젝트 구조
### 어플리케이션 코드
- Backend
	- API 서버 구현: FastAPI
	- 빅데이터:
		- 연산: Numpy, Scipy ... (+ Pandas 사용 지양)
		- 모델링: Xarray, Zarr, Dask (파일 기반 캐싱)
	- 데이터 수집:
		- Financial Modeling Prep API, World Bank API
	- 데이터 저장:
		- 파일 시스템: 연산용 데이터 (금융 데이터, 캐싱 등)
		- Postgresql: 비즈니스용 데이터 (고객관리, 커텐츠 등)
	- 국제화를 위한 다국어 제공 도구:
		- Google Translate API (from GCP)
- Frontend
	- 어플리케이션 작성: Svelte + TypeScript
		- 번들러: rollup
		- SPA 형태로 만들 예정  
		(SSR을 위해서 별도의 렌딩 페이지를 Jinja2 템플릿 엔진으로 만들까 고민중)
	- 데이터 시각화: Apache Echarts
	- 호스팅: 별도의 서버 없이 Backend에서 호스팅
- 결제 시스템: Toss Payments

### 서버 인프라
- 클라우드 서비스: AWS
- 클라우드 아키텍처: 
	- 목적: 최대한 단순한 구조로 무제한 확장성과 비용 지출 최적화
	- ALB: Route53 -> **ALB** -> ECS(컨테이너들)
		- HTTPS 요청 복호화 & 로드 벨런싱
	- ECS(Fargate): 코드 실행
		- 수평 확장을 통한 오토스케일링
	- EFS: 파일 시스템으로 사용 (ECS Task에 볼륨으로 마운트)
		- 용량 무제한
		- ECS가 수평 확장되어도 파일 시스템의 일관성 유지
	- RDS(Aurora Postgresql)
		- 수직 확장을 통한 오토스케일링
		- 데이터 양과 연산량이 적은 비즈니스용 데이터에만 사용
	- Secret Manager
		- 보안데이터 통합 관리
- CI/CD: GitHub Actions
	- push -> Docker 빌드 -> ECR로 배포 -> ECS 서비스 생성 & 기존 서비스 중지