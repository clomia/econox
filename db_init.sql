--- Last commit: 2023-09-05 14:39:52 ---
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

------------------------------------------------
-- 유저
------------------------------------------------
CREATE TYPE membership AS ENUM('basic', 'professional');
CREATE TYPE currency AS ENUM('KRW', 'USD');

CREATE TABLE users (
    "id" UUID PRIMARY KEY, -- Cognito id
    "email" VARCHAR(255) NOT NULL UNIQUE,
    "name" VARCHAR(255) NOT NULL, -- 회원가입시 자동생성, 이후 수정
    "phone" VARCHAR(255) NOT NULL, -- AWS SNS 전송에 사용 가능한 문자열
    "membership" membership NOT NULL, 
    "membership_expiration" TIMESTAMP NOT NULL, -- 다음 결제 일시
    "currency" currency NOT NULL, 
    "tosspayments_billing_key" VARCHAR(255), 
    "paypal_token" VARCHAR(255), -- facilitatorAccessToken
    "paypal_subscription_id" VARCHAR(255), 
    "billing_date" INT NOT NULL, -- 일  (맴버십 시작일 기록)
    "billing_time" TIME NOT NULL, -- 시:분:초  (맴버십 시작시간 기록)
    "created" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP 
); 
-- (email -> user) 검색 최적화 관련: email 필드에 UNIQUE속성 있어서 자동으로 인덱스 생성되므로 별도의 인덱스 생성 불필요

------------------------------------------------
-- 회원가입 내역 (중복 회원가입 판별용)
------------------------------------------------
CREATE TABLE signup_histories (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "email" VARCHAR(255) NOT NULL,
    "phone" VARCHAR(255) NOT NULL,
    "created" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP 
);

------------------------------------------------
-- Tosspayments 청구 내역
------------------------------------------------
CREATE TABLE tosspayments_billings (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "user_id" UUID REFERENCES users(id) ON DELETE CASCADE,
    "order_id" UUID NOT NULL, -- 우리가 발급
    "payment_key" VARCHAR(255) NOT NULL, -- Toss가 발급
    "order_name" VARCHAR(255) NOT NULL, -- 상품명
    "total_amount" INT NOT NULL, -- 고객이 결제한 금액
    "supply_price" INT NOT NULL,  -- 공급가액
    "vat" INT NOT NULL, -- 부가세
    "card_issuer" VARCHAR(50) NOT NULL, -- 카드 발급사
    "card_acquirer" VARCHAR(50) NOT NULL, -- 카드 매입사
    "card_number_masked" VARCHAR(50) NOT NULL, -- 가려진 카드번호
    "card_approve_number" VARCHAR(50) NOT NULL, -- 카드사 승인 번호
    "card_type" VARCHAR(50) NOT NULL, -- 신용/체크 타입
    "card_owner_type" VARCHAR(50) NOT NULL, -- 개인/법인 타입
    "receipt_url" TEXT NOT NULL, -- 영수증 URL
    "created" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP 
)