--- Last commit: 2023-12-04 17:13:03 ---
CREATE TABLE deepl (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "from_lang" VARCHAR(3),
    "from_text" TEXT NOT NULL,
    "to_lang" VARCHAR(3) NOT NULL,
    "to_text" TEXT NOT NULL,
    "created" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP 
);

CREATE INDEX idx_deepl_to_text ON deepl (from_lang, to_lang, from_text);
-- [인덱스 사용 예시]
-- SELECT to_text FROM deepl WHERE from_lang = 'ENG' AND to_lang = 'KOR' AND from_text = 'Hello, world!';