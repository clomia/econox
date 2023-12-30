--- Last commit: 2023-12-30 13:15:10 ---
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

------------------------------------------------
-- 유저
------------------------------------------------
CREATE TYPE membership AS ENUM('basic', 'professional');
CREATE TYPE currency AS ENUM('KRW', 'USD');
CREATE TYPE billing_status AS ENUM('active', 'require', 'deactive'); -- 정상/미결제/정지

CREATE TABLE users (
    "id" UUID PRIMARY KEY, -- Cognito id
    "email" VARCHAR(255) NOT NULL UNIQUE,
    "name" VARCHAR(255) NOT NULL, -- 회원가입시 자동생성, 이후 수정
    "phone" VARCHAR(255) NOT NULL, -- AWS SNS 전송에 사용 가능한 문자열
    "membership" membership NOT NULL,  
    "currency" currency NOT NULL,  
    "origin_billing_date" TIMESTAMP, -- 확정된 기준날짜 (실제로 결제가 발생하여 확정되면 반영됨)
    "base_billing_date" TIMESTAMP, -- 계산된 기준날짜 (결제 시작 혹은 결제일 변경 시 계산 결과가 바로 반영됨)
    "current_billing_date" TIMESTAMP,  -- 최근 청구 날짜 
    "next_billing_date" TIMESTAMP NOT NULL, -- 다음 청구 날짜
    "tosspayments_billing_key" VARCHAR(255), 
    "paypal_subscription_id" VARCHAR(255), 
    "billing_method" VARCHAR(255), 
    "billing_status" billing_status DEFAULT 'active',
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
-- Tosspayments 청구 내역
------------------------------------------------
CREATE TABLE tosspayments_billings (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "user_id" UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    "order_id" UUID NOT NULL, -- 우리가 발급
    "transaction_time" TIMESTAMP NOT NULL, 
    "payment_key" VARCHAR(255) NOT NULL, -- Toss가 발급
    "order_name" VARCHAR(255) NOT NULL, -- 상품명
    "total_amount" DECIMAL(15, 5) NOT NULL, -- 고객이 결제한 금액
    "supply_price" DECIMAL(15, 5) NOT NULL,  -- 공급가액
    "vat" DECIMAL(15, 5) NOT NULL, -- 부가세
    "card_issuer" VARCHAR(50) NOT NULL, -- 카드 발급사
    "card_acquirer" VARCHAR(50) NOT NULL, -- 카드 매입사
    "card_number_masked" VARCHAR(50) NOT NULL, -- 가려진 카드번호
    "card_approve_number" VARCHAR(50) NOT NULL, -- 카드사 승인 번호
    "card_type" VARCHAR(50) NOT NULL, -- 신용/체크 타입
    "card_owner_type" VARCHAR(50) NOT NULL, -- 개인/법인 타입
    "receipt_url" TEXT NOT NULL, -- 영수증 URL
    "created" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP 
);
CREATE INDEX idx_tosspayments_billings_user_id ON tosspayments_billings(user_id);

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
CREATE TYPE element_section AS ENUM('symbol', 'country', 'custom');
CREATE TABLE elements (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "section" element_section NOT NULL,
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