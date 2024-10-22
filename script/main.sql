--- Last commit: 2024-03-26 16:31:27 ---
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

------------------------------------------------
-- 유저
------------------------------------------------
CREATE TABLE users (
    "id" UUID PRIMARY KEY, -- Cognito id
    "email" VARCHAR(255) NOT NULL UNIQUE,
    "name" VARCHAR(255) NOT NULL, -- 회원가입시 자동생성, 이후 수정
    "phone" VARCHAR(255) NOT NULL, -- AWS SNS 전송에 사용 가능한 문자열
    "membership" VARCHAR(255) NOT NULL,  
    "currency" VARCHAR(3) NOT NULL,  
    "origin_billing_date" TIMESTAMP, -- 확정된 기준날짜 (실제로 결제가 발생하여 확정되면 반영됨)
    "base_billing_date" TIMESTAMP, -- 계산된 기준날짜 (결제 시작 혹은 결제일 변경 시 계산 결과가 바로 반영됨)
    "current_billing_date" TIMESTAMP,  -- 최근 청구 날짜 
    "next_billing_date" TIMESTAMP NOT NULL, -- 다음 청구 날짜
    "port_one_billing_key" VARCHAR(255), 
    "paypal_subscription_id" VARCHAR(255), 
    "billing_method" VARCHAR(255), 
    "billing_status" VARCHAR(255) DEFAULT 'active',
    "created" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP 
); 
CREATE INDEX idx_users_paypal_subscription_id ON users (paypal_subscription_id);
-- (email -> user) 검색 최적화 관련: email 필드에 UNIQUE속성 있어서 자동으로 인덱스 생성되므로 별도의 인덱스 생성 불필요
-- 기준 날짜란: 구독 결제 시작일 혹은 변경일이다. 다음 청구일을 정확하게 계산하려면 꼭 필요한 값이다. (날짜 계산시 발생하는 예외 처리를 위해 필요함)

------------------------------------------------
-- 회원가입 내역 (중복 회원가입 판별용)
------------------------------------------------
CREATE TABLE signup_histories (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "user_id" UUID NOT NULL,
    "user_deleted" TIMESTAMP,
    "email" TEXT NOT NULL,
    "phone" TEXT NOT NULL,
    "created" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP 
);

------------------------------------------------
-- 포트원 청구 내역
------------------------------------------------
CREATE TABLE port_one_billings (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "user_id" UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    "payment_id" VARCHAR(255) NOT NULL, -- 우리가 발급
    "transaction_time" TIMESTAMP NOT NULL, 
    "pg_tx_id" VARCHAR(255) NOT NULL, -- PG사에서 발급
    "order_name" VARCHAR(255) NOT NULL, -- 상품명
    "total_amount" DECIMAL(15, 5) NOT NULL, -- 고객이 결제한 금액
    "card_number_masked" VARCHAR(50) NOT NULL, -- 가려진 카드번호
    "created" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP 
);
CREATE INDEX idx_port_one_billings_user_id ON port_one_billings(user_id);

------------------------------------------------
-- PayPal 청구 내역
------------------------------------------------
CREATE TABLE paypal_billings (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "user_id" UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    "transaction_id" VARCHAR(60) UNIQUE NOT NULL, -- 멱등키로 사용
    "transaction_time" TIMESTAMP NOT NULL,
    "order_name" VARCHAR(255) NOT NULL, -- 상품명
    "total_amount" DECIMAL(15, 5) NOT NULL, -- 고객이 결제한 금액
    "fee_amount" DECIMAL(15, 5) NOT NULL, -- PayPal 수수료
    "created" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP 
);
CREATE INDEX idx_paypal_billings_user_id ON paypal_billings(user_id);

------------------------------------------------
-- 요소들
------------------------------------------------
CREATE TABLE elements (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "section" VARCHAR(255) NOT NULL,
    "code" VARCHAR(255) NOT NULL,
    UNIQUE ("section", "code") -- 이 순서가 인덱스 효율적임
);

------------------------------------------------
-- 펙터들
------------------------------------------------
CREATE TABLE factors (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "section" VARCHAR(255) NOT NULL, -- factor가 속한 클래스
    "code" VARCHAR(255) NOT NULL, -- factor의 변수명
    "name" VARCHAR(255) NOT NULL, -- 노출되는 이름
    "note" TEXT NOT NULL, -- 설명
    UNIQUE ("section", "code")
);

-----------------------------------------------
-- 유저가 선택하여 단변량 툴에 추가된 요소들
------------------------------------------------
CREATE TABLE users_elements (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "user_id" UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    "element_id" INT NOT NULL REFERENCES elements(id) ON DELETE CASCADE,
    "created" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE ("user_id", "element_id")
);
CREATE INDEX idx_users_elements_user_id ON users_elements(user_id);
CREATE INDEX idx_users_elements_element_id ON users_elements(element_id);

------------------------------------------------
-- 요소에 대해 유효한 펙터들
-- 이 테이블의 레코드가 피쳐(요소의 펙터)입니다.
------------------------------------------------
CREATE TABLE elements_factors (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "element_id" INT NOT NULL REFERENCES elements(id) ON DELETE CASCADE,
    "factor_id" INT NOT NULL REFERENCES factors(id) ON DELETE CASCADE,
    "created" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE ("element_id", "factor_id")
);
CREATE INDEX idx_elements_factors_element_id ON elements_factors(element_id);
CREATE INDEX idx_elements_factors_factor_id ON elements_factors(factor_id);

------------------------------------------------
-- 유저가 소유한 피쳐 그룹
------------------------------------------------
CREATE TABLE feature_groups (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "user_id" UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    "name" VARCHAR(255) NOT NULL, -- 그룹명
    "description" TEXT DEFAULT NULL, -- 그룹에 대한 설명
    "chart_type" VARCHAR(255) NOT NULL DEFAULT 'line', -- 기본 차트 타입
    "public" BOOLEAN NOT NULL DEFAULT FALSE, -- 공유 여부
    "created" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_feature_groups_user_id ON feature_groups(user_id);

------------------------------------------------
-- 피쳐 그룹이 소유한 피쳐들
------------------------------------------------
CREATE TABLE feature_groups_features (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "feature_group_id" INT NOT NULL REFERENCES feature_groups(id) ON DELETE CASCADE,
    "feature_id" INT NOT NULL REFERENCES elements_factors(id) ON DELETE CASCADE,
    "feature_color" VARCHAR(255) NOT NULL, -- 피쳐 색상 (CSS에서 사용 가능한 문자열)
    "created" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE ("feature_group_id", "feature_id") -- 하나의 피쳐 그룹에 피쳐가 중복되지 않도록
);
CREATE INDEX idx_feature_groups_features_feature_group_id ON feature_groups_features(feature_group_id);