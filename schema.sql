--- Last commit: 2023-07-25 10:52:03 ---
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

------------------------------------------------
-- Cognito, TossPayments 기반 유저 (모든 정보가 Confirm되면 생성됨)
------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    "id" UUID PRIMARY KEY, -- Cognito id를 사용
    "email" VARCHAR(255) NOT NULL UNIQUE, -- Confirm 필수 
    "name" VARCHAR(255) NOT NULL, -- 회원가입시 자동생성, 이후 수정
    "billing_key" VARCHAR(255) NOT NULL, -- 회원가입시 결제 정보를 통해 TossPayments가 생성
    "membership_type" VARCHAR(255) NOT NULL, -- 회원가입시 생성, 이후 갱신
    "membership_expire" TIMESTAMP NOT NULL, -- 회원가입시 생성, 이후 갱신
    "created" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP 
); 
-- (email -> user) 검색 최적화 관련: email 필드에 UNIQUE속성 있어서 자동으로 인덱스 생성되므로 별도의 인덱스 생성 불필요

------------------------------------------------
-- 결제 내역 (유저의 결제 내역을 가져오기 위한 최소한의 정보)
------------------------------------------------
CREATE TABLE IF NOT EXISTS payments (
    "id" UUID PRIMARY KEY DEFAULT uuid_generate_v4(), -- TossPayments orderId로 사용
    "user_id" UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE, -- TossPayments customerKey로 사용
    "payment_key" VARCHAR(255) NOT NULL, -- 토스가 발급한 결제식별자
    "created" TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS payments_user_index ON payments("user_id"); -- user에 대한 payments 검색용

------------------------------------------------
-- 카드 등록 내역 (개인정보 없이 중복 회원가입 감지용)
------------------------------------------------
CREATE TABLE IF NOT EXISTS card_history (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "token" BYTEA NOT NULL, -- 카드정보가 단방향 해시된 bytes
    "created" TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS card_history_token_index ON card_history("token");