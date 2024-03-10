<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import GraphGen from "./GraphGen.svelte";
  import LinesGen from "./line-gen/Index.svelte";
  import Earth from "./Earth.svelte";
  import TxtEffect from "./TxtEffect.svelte";
  import ReflectiveButton from "../../components/ReflectiveButton.svelte";
  import ToggleArrow from "../../assets/icon/ToggleArrow.svelte";
  import { isInViewport } from "../../modules/functions";

  let introMain: HTMLElement;
  let page2: HTMLElement;
  let page1desc: HTMLElement;

  let toggleOn = true;
  let page2DescOn = false;
  const scrollHandler = () => {
    // 현재 스크롤상 화면이 introMain보다 위에 있을때만 토글 버튼이 활성화되도록 한다.
    // 한번 비활성화되면 다시 활성화되지 않아야 한다.
    const eleRect = introMain.getBoundingClientRect();
    const eleTop = eleRect.top + window.scrollY;
    const eleScrollYRefTop = eleTop + eleRect.height - window.innerHeight;
    if (window.scrollY > eleScrollYRefTop + 5) {
      // 5는 그냥 버퍼임
      toggleOn = false;
    }
    page2DescOn = !isInViewport(page1desc);
  };
  const scrollPage2 = () => {
    page2.scrollIntoView({ behavior: "smooth", block: "end" });
  };
  $: console.log(page2DescOn);

  onMount(() => {
    // 단색으로 해야 세밀한 조작에 유리함
    const color = "rgb(31, 48, 54)";
    document.documentElement.style.background = color;
    document.body.style.background = color;
    document.body.style.paddingBottom = "0";
    introMain.scrollIntoView({ behavior: "instant", block: "end" });
    window.addEventListener("scroll", scrollHandler);
  });
  onDestroy(() => {
    document.documentElement.style.background = "";
    document.body.style.background = "";
    document.body.style.paddingBottom = "";
  });
  const introBottomText = ["주가", "매출", "부채", "직원 수"];
</script>

<section class="page1">
  <div class="intro-main" bind:this={introMain}>
    <div class="intro-main__subtitle">다변량</div>
    <div class="intro-main__title">시계열 비교 분석</div>

    <button class="intro-main__start-btn">
      <ReflectiveButton text="무료로 시작하기" color="rgb(230, 230, 230)" />
    </button>

    <div class="intro-main__bottom-text">
      <div class="intro-main__bottom-text__main">
        <TxtEffect
          txtArr={introBottomText}
          size="2rem"
          color="rgb(230, 230, 230)"
        />
      </div>
      <div
        class="intro-main__bottom-text__desc"
        class:page2__desc_off={page2DescOn}
        bind:this={page1desc}
      >
        이코녹스는 전 세계 기업의 방대한 시계열 데이터를 제공합니다
      </div>
    </div>
    {#if toggleOn}
      <button class="intro-main__bottom-btn" on:click={scrollPage2}>
        <ToggleArrow />
      </button>
    {/if}
  </div>
  <GraphGen width="100%" height="100%" />
</section>

<section class="page2" bind:this={page2}>
  <div class="page2__desc" class:page2__desc_on={page2DescOn}>
    이코녹스는 전 세계 기업의 방대한 시계열 데이터를 제공합니다
  </div>
  <div class="multiline-chart">
    <LinesGen width="100%" height="60%" />
  </div>
  <div class="earth">
    <div class="earch-front" />
    <div class="earth-main">
      <Earth width="30vw" height="30vw" distance={150} />
    </div>
    <div class="earth-behind">
      <div class="earth-behind__gradient" />
    </div>
  </div>
</section>

<section class="page3">안녕하세요</section>

<style>
  :root {
    /* 스크롤바 너비는 0.4rem으로 설정되어 있음 */
    --max-vw: calc(100vw - 0.4rem);
    /* 투명하면 겹쳐보이니까 불투명한 색 별도로 정의 */
    --text-color: rgb(230, 230, 230);
  }
  .page1 {
    position: relative;
    background: linear-gradient(
      to bottom,
      rgba(0, 0, 0, 0) 0%,
      rgba(32, 34, 36) 20%,
      rgba(22, 24, 26) 50%,
      rgb(10, 10, 11) 100%
    );
    height: 100vh;
    width: var(--max-vw);
  }
  .page2 {
    position: relative;
    height: 100vh;
    width: var(--max-vw);
    background-color: rgb(10, 10, 11);
  }
  .page3 {
    position: absolute;
    left: 0;
    bottom: 0;
    width: 100%;
    height: 2rem;
    background-color: red;
  }
  .intro-main {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 1;
    color: var(--text-color);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: linear-gradient(
      to bottom,
      black 0%,
      rgb(31, 48, 54) 0%,
      rgba(0, 0, 0, 0) 10%,
      rgba(0, 0, 0, 0) 90%,
      rgb(10, 10, 11) 100%
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
    margin-top: 4rem;
    margin-bottom: 6%;
  }
  .intro-main__start-btn:hover {
    cursor: pointer;
  }

  .intro-main__bottom-text {
    position: absolute;
    bottom: 10%;
    width: 100%;
  }
  .intro-main__bottom-text__main,
  .intro-main__bottom-text__desc {
    display: flex;
    justify-content: center;
  }
  .intro-main__bottom-text__desc {
    display: flex;
    justify-content: center;
    margin-top: 2rem;
    color: var(--text-color);
    font-size: 1.3rem;
    opacity: 1;
    transition: opacity 1s ease-in;
  }
  .page2__desc_off {
    opacity: 0;
    transition: none;
  }
  .intro-main__bottom-btn {
    position: absolute;
    bottom: 0;
    width: 100%;
    height: 3rem;
    display: flex;
    justify-content: center;
    align-items: center;
    opacity: 0.2;
    padding-bottom: 2rem;
    padding-top: 3rem;
  }
  .intro-main__bottom-btn:hover {
    cursor: pointer;
    opacity: 1;
    background: linear-gradient(
      to bottom,
      rgba(0, 0, 0, 0) 0%,
      rgba(255, 255, 255, 0.03) 100%
    );
  }
  .multiline-chart {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0.4;
  }
  .earth-main,
  .earth-behind,
  .earch-front {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .earth-main {
    z-index: 10;
  }
  .earth-behind {
    z-index: 9;
  }
  .earch-front {
    z-index: 11;
  }
  .earth-behind__gradient {
    width: 100vmax;
    height: 100vmax;
    background: radial-gradient(
      rgba(0, 0, 0, 1) 0%,
      rgba(0, 0, 0, 0) 40%,
      rgba(0, 0, 0, 0) 100%
    );
  }
  .page2__desc {
    position: absolute;
    top: 2rem;
    left: 0;
    width: 100%;
    display: flex;
    justify-content: center;
    z-index: 20;
    color: var(--text-color);
    font-size: 1.6rem;
    opacity: 0;
    transition: none;
  }
  .page2__desc_on {
    opacity: 1;
    transition: opacity 1s ease-in;
  }
</style>
