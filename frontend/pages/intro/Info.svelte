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
</main>

<style>
  main {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
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
    padding: 5rem;
  }
  .tags span {
    color: rgba(255, 255, 255, 0.7);
    white-space: nowrap;
    padding: 0.2rem 1rem;
    display: flex;
    align-items: center;
  }
</style>
