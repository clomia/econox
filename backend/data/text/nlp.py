import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def split_paragraph(text, threshold=0.15):  # 일단 정확도 떨어져서 못씀
    """줄바꿈 없는 긴 글을 문단으로 나눠 줄바꿈을 삽입합니다."""
    # 괄호와 그 내용을 임시 문자열로 대체
    brackets = re.findall(r"\([^)]*\)", text)
    for idx, bracket in enumerate(brackets):
        text = text.replace(bracket, f" BRACKETPLACEHOLDER{idx} ")

    # 문장으로 나눔
    sentences = [s.strip() for s in text.split(".") if s]

    # TF-IDF 벡터화 및 문장 중요도 평가
    vectorizer = TfidfVectorizer().fit_transform(sentences)
    sentence_importance = vectorizer.sum(axis=1).tolist()
    sorted_importance = sorted(sentence_importance, reverse=True)

    # 문장 간의 코사인 유사도 계산
    cosine_matrix = cosine_similarity(vectorizer)

    # 문단을 나누기 위한 인덱스를 저장할 리스트
    paragraph_breaks = []

    # 중요도가 높은 문장은 별도의 문단으로 분리
    for i, importance in enumerate(sentence_importance):
        if importance in sorted_importance[: len(sentences) // 4]:  # 상위 25% 중요도 문장
            paragraph_breaks.append(i)

    # 유사도 기반으로 문단 분리
    for i in range(1, len(cosine_matrix)):
        if cosine_matrix[i - 1][i] < threshold and i not in paragraph_breaks:
            paragraph_breaks.append(i)

    # 문단으로 나누기
    paragraphs = []
    start = 0
    for index in sorted(paragraph_breaks):
        paragraphs.append(" ".join(sentences[start:index]))
        start = index
    paragraphs.append(" ".join(sentences[start:]))

    # 결과에서 임시 문자열을 원래 괄호 내용으로 대체
    result = "\n".join(paragraphs)
    for idx, bracket in enumerate(brackets):
        result = result.replace(f"BRACKETPLACEHOLDER{idx}", bracket)

    return result
