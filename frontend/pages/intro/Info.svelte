<script lang="ts">
  import TiltedCheck from "../../assets/icon/TiltedCheck.svelte";
</script>

<main>
  <section class="tags">
    <span>
      <div class="check-icon"><TiltedCheck /></div>
      주식, ETF, 뮤추얼 펀드, 지수, 원자재, 외환 및 암호 화폐
    </span>
    <span>
      <div class="check-icon"><TiltedCheck /></div>
      전 세계 46개국 90개 이상의 거래소 접근
    </span>
    <span>
      <div class="check-icon"><TiltedCheck /></div>
      50,000개 이상의 증권 데이터
    </span>
    <span>
      <div class="check-icon"><TiltedCheck /></div>
      30년 이상의 주식 과거 가격 데이터
    </span>
    <span>
      <div class="check-icon"><TiltedCheck /></div>
      20년 이상의 과거 원자재 및 외환 데이터
    </span>
    <span>
      <div class="check-icon"><TiltedCheck /></div>
      국제 신고를 포함한 15년 이상의 재무제표 데이터
    </span>
  </section>
  <section class="benefits">
    첫 회원가입 시 결제정보 등록 없이 3일간 모든 기능을 제공합니다
  </section>
  <section class="cost">
    <div class="cost__title">비용</div>
    <div class="cost-grid">
      <div class="cost-type">일반 맴버십</div>
      <div>월 16,900원</div>
      <div>데이터 다운로드를 제외한 모든 기능</div>
      <div class="cost-type">전문가 맴버십</div>
      <div>월 19,900원</div>
      <div>무제한 데이터 다운로드를 포함한 모든 기능</div>
    </div>
  </section>
  <section class="extra">
    <div class="extra__title">데이터 다운로드</div>
    <div class="extra__content1">
      전문가 맴버십을 구독하면 모든 시계열 데이터를 xlsx와 csv파일로 내려받을 수
      있습니다.
    </div>
    <div class="extra__content2">
      엑셀과 데이터 분석부터 인공지능 학습까지 원하는 용도로 마음껏 사용하세요.
    </div>
  </section>
</main>

<style>
  main {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    color: rgba(255, 255, 255, 0.7);
  }
  .check-icon {
    opacity: 0.6;
    padding-right: 0.4rem;
  }
  .tags {
    width: 100%;
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    padding: 0 5rem;
  }
  .tags span {
    white-space: nowrap;
    padding: 0.2rem 1rem;
    display: flex;
    align-items: center;
  }
  .benefits {
    font-size: 1.2rem;
    color: rgba(255, 255, 255, 0.8);
    margin-top: 3rem;
    padding: 0 2rem;
  }
  .cost {
    margin-top: 1.5rem;
    padding: 0 2rem;
  }
  .cost__title {
    display: flex;
    width: 100%;
    justify-content: center;
    font-size: 1.5rem;
    padding-bottom: 0.5rem;
  }
  .cost-grid {
    display: grid;
    grid-template-columns: repeat(3, auto);
    grid-template-rows: repeat(2, auto);
    row-gap: 3px;
  }
  .cost-grid > :nth-child(-n + 3) {
    border-bottom: thin solid rgba(255, 255, 255, 0.2);
    padding-bottom: 3px;
  }
  .cost-grid div {
    padding-right: 0.5rem;
  }
  .extra {
    margin-top: 2rem;
    padding-bottom: 2rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 100%;
  }
  .extra__title {
    font-size: 1.3rem;
    padding-bottom: 0.5rem;
  }
  .extra__content1 {
    padding-bottom: 0.5rem;
  }
  .extra__content1,
  .extra__content2 {
    padding: 0 2rem;
  }
</style>
