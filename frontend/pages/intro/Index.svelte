<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { Text, Lang, IntroMounted } from "../../modules/state";
  import GraphGen from "./GraphGen.svelte";
  import LinesGen from "./line-gen/Index.svelte";
  import Earth from "./Earth.svelte";
  import TxtEffect from "./TxtEffect.svelte";
  import ReflectiveButton from "../../components/ReflectiveButton.svelte";
  import ToggleArrow from "../../assets/icon/ToggleArrow.svelte";
  import { isInViewport } from "../../modules/functions";
  import { introBottomText, footerText } from "./text";

  let introMain: HTMLElement;
  let page2: HTMLElement;
  let page1desc: HTMLElement;
  let page2TextTop: HTMLElement;
  let page2TextBottom: HTMLElement;
  let page2DescHeight: number = 0;

  let toggleOn = true;
  let page2DescOn = false;
  let page2TextTopOn = false;
  let page2TextBottomOn = false;
  const scrollHandler = () => {
    if (!introMain) {
      return;
    }
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
    page2TextTopOn = isInViewport(page2TextTop);
    page2TextBottomOn = isInViewport(page2TextBottom);
  };
  const scrollPage2 = () => {
    page2.scrollIntoView({ behavior: "smooth", block: "end" });
  };

  onMount(() => {
    // 리소스 정리 문제로 인해 여러번 마운트될 수 없음
    if ($IntroMounted) location.reload();
    $IntroMounted = true;
    // 단색으로 해야 세밀한 조작에 유리함
    const color = "rgb(31, 48, 54)";
    document.body.style.background = color;
    document.body.style.paddingBottom = "0";
    document.body.style.overflowX = "clip";
    document.body.style.minWidth = "100%";
    introMain.scrollIntoView({ behavior: "instant", block: "end" });
    window.addEventListener("scroll", scrollHandler);
  });
  onDestroy(() => {
    document.body.style.background = "";
    document.body.style.paddingBottom = "";
    document.body.style.overflowX = "";
    document.body.style.minWidth = "";
  });

  $: page2TextTopPx = page2DescHeight + 40;
</script>

<section class="page1">
  <div class="intro-main" bind:this={introMain}>
    <div class="intro-main__subtitle">{$Text.Multivariate}</div>
    <div class="intro-main__title">{$Text.IntroTitle}</div>

    <button class="intro-main__start-btn">
      <ReflectiveButton
        text={$Text.IntroStartButton}
        color="rgb(230, 230, 230)"
      />
    </button>

    <div class="intro-main__bottom-text">
      <div class="intro-main__bottom-text__main">
        <TxtEffect
          txtArr={introBottomText[$Lang]}
          size="1.6rem"
          color="rgb(230, 230, 230)"
        />
      </div>
      <div
        class="intro-main__bottom-text__desc"
        class:page2__desc_off={page2DescOn}
        bind:this={page1desc}
      >
        {$Text.IntroPage1Desc}
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
  <div
    class="page2__desc"
    bind:clientHeight={page2DescHeight}
    class:page2__desc_on={page2DescOn}
  >
    {$Text.IntroPage2Desc}
  </div>
  <div
    class="page2__text-top"
    bind:this={page2TextTop}
    style="top: {page2DescOn ? page2TextTopPx : 0}px;"
    class:page2-text-on={page2TextTopOn}
    class:page2__text-top-up={!page2DescOn}
  >
    <p>{$Text.IntroPage2TopP1}</p>
    <p>{$Text.IntroPage2TopP2}</p>
  </div>
  <div
    class="page2__text-bottom"
    bind:this={page2TextBottom}
    class:page2-text-on={page2TextBottomOn}
  >
    <p>{$Text.IntroPage2BottomP1}</p>
    <p>{$Text.IntroPage2BottomP2}</p>
  </div>
  <div class="multiline-chart-front" />
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
  <div class="page2__bottom" />
</section>

<section class="page3">
  <div class="footer">
    <div class="footer__r1">
      <img
        src="/static/img/favicon.png"
        alt="logo icon"
        height="30px"
        style="margin-right: 1rem;"
      />
      Copyright © Econox. All Rights Reserved
    </div>
    <div class="footer__r2">{footerText[$Lang][0]}</div>
    <div class="footer__r3">{footerText[$Lang][1]}</div>
    <div class="footer__r4">{footerText[$Lang][2]}</div>
    <div class="footer__r5">
      <a href="https://www.econox.wiki">{footerText[$Lang][3]}</a>
    </div>
  </div>
</section>

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
    position: relative;
    width: var(--max-vw);
    background-color: rgb(10, 10, 11);
    z-index: 10;
    display: flex;
    justify-content: center;
    color: rgb(201, 201, 201);
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
    font-size: max(2rem, 2.5vw);
    color: white;
    text-align: center;
  }
  .intro-main__title {
    margin-top: 0.5rem;
    font-size: max(2.5rem, 3.5vw);
    color: white;
    text-align: center;
    padding: 0 2rem;
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
    text-align: center;
    padding: 0 2rem;
  }
  .intro-main__bottom-text__desc {
    display: flex;
    justify-content: center;
    margin-top: 2rem;
    color: var(--text-color);
    font-size: 1.4rem;
    opacity: 1;
    transition: opacity 500ms ease-in;
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
    opacity: 0.7;
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
  .multiline-chart-front {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 1;
    background: linear-gradient(
      to right,
      rgb(10, 10, 11) 15%,
      rgba(0, 0, 0, 0) 20%,
      rgba(0, 0, 0, 0) 80%,
      rgb(10, 10, 11) 85%
    );
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
    overflow: hidden;
  }
  .earth-main {
    z-index: 8;
  }
  .earth-behind {
    z-index: 7;
  }
  .earch-front {
    z-index: 9;
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
    z-index: 10;
    color: var(--text-color);
    font-size: max(1.5rem, 1.5vw);
    opacity: 0;
    transition: none;
    text-align: center;
    padding: 0 2rem;
  }
  .page2__desc_on {
    opacity: 1;
    transition: opacity 500ms ease-in;
  }
  .page2__text-top,
  .page2__text-bottom {
    position: absolute;
    left: 0;
    width: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    z-index: 10;
    color: var(--text-color);
    font-size: 1.1rem;
    opacity: 0;
    transition:
      opacity 200ms ease-in,
      top 100ms ease-in-out;
    text-align: center;
    padding: 0 2rem;
  }
  .page2-text-on {
    opacity: 1;
  }
  .page2__text-top {
    opacity: 0.8;
  }
  .page2__text-top-up {
    top: 0rem;
    font-size: 1.4rem;
    opacity: 1;
  }
  .page2__text-bottom {
    bottom: 2rem;
    font-size: 1.4rem;
  }
  .page2__bottom {
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 1px;
    background-color: rgb(157, 157, 157);
    z-index: 12;
    opacity: 0.4;
  }
  .footer {
    padding: 2rem 1rem;
    padding-bottom: 5.5rem;
  }
  .footer__r1 {
    font-size: 1.1rem;
    padding-bottom: 1rem;
    display: flex;
    align-items: center;
    color: var(--text-color);
  }
  .footer__r2,
  .footer__r3,
  .footer__r4 {
    font-size: 14px;
  }

  .footer__r5 {
    margin-top: 0.5rem;
  }
  .footer__r5 a {
    color: rgb(217, 217, 234);
    text-decoration: none;
  }
  .footer__r5 a:hover {
    cursor: pointer;
    text-decoration: underline;
  }
</style>
