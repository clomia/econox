<script lang="ts">
  import GraphGen from "./GraphGen.svelte";
</script>

<section class="page1">
  <div class="intro-main">
    <div class="intro-main__subtitle">다변량</div>
    <div class="intro-main__title">시계열 비교 분석</div>
    <button class="intro-main__start-btn">무료로 시작하기</button>
  </div>
  <GraphGen width="100%" height="100%" />
</section>

<style>
  :root {
    /* 스크롤바 너비는 0.4rem으로 설정되어 있음 */
    --max-vw: calc(100vw - 0.4rem);
  }
  .page1 {
    position: relative;
    background: linear-gradient(
      to bottom,
      rgba(0, 0, 0, 0) 0%,
      rgba(32, 34, 36) 20%,
      rgba(22, 24, 26) 50%,
      rgba(32, 34, 36) 80%,
      rgba(0, 0, 0, 0) 100%
    );
    height: 100vh;
    width: var(--max-vw);
  }
  .intro-main {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 10;
    color: var(--white);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: linear-gradient(
      to bottom,
      rgb(31, 40, 45) 0%,
      rgba(0, 0, 0, 0) 5%,
      rgba(0, 0, 0, 0) 100%
    );
  }
  .intro-main__subtitle {
    font-size: 2.25rem;
  }
  .intro-main__title {
    margin-top: 0.5rem;
    font-size: 3.5rem;
  }
  .intro-main__start-btn {
    margin-top: 3rem;
    padding: 0.5rem 1rem;
    border-radius: 0.2rem;
    color: white;
    background: var(--widget-background);
    border: thin solid white;
    opacity: 0.6;
  }
  .intro-main__start-btn:hover {
    cursor: pointer;
    opacity: 1;
  }
</style>
