<!-- 이 컴포넌트는 전체 창 로딩 에니메이션 용이며, 활성화되어있는 동안 스크롤이 잠깁니다! -->
<script>
  import { onMount, onDestroy } from "svelte";
  onMount(() => (document.body.style.overflow = "hidden"));
  onDestroy(() => (document.body.style.overflow = ""));
</script>

<div id="preloader">
  <div id="loader" />
</div>

<style>
  #preloader {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    line-height: 1;
  }
  #loader {
    display: block;
    position: relative;
    left: 50%;
    top: 50%;
    width: 150px;
    height: 150px;
    margin: -75px 0 0 -75px;
    border-radius: 50%;
    border: 3px solid transparent;
    border-top-color: #9370db;
    -webkit-animation: spin 2s linear infinite;
    animation: spin 2s linear infinite;
  }
  #loader:before {
    content: "";
    position: absolute;
    top: 5px;
    left: 5px;
    right: 5px;
    bottom: 5px;
    border-radius: 50%;
    border: 3px solid transparent;
    border-top-color: #ba55d3;
    -webkit-animation: spin 3s linear infinite;
    animation: spin 3s linear infinite;
  }
  #loader:after {
    content: "";
    position: absolute;
    top: 15px;
    left: 15px;
    right: 15px;
    bottom: 15px;
    border-radius: 50%;
    border: 3px solid transparent;
    border-top-color: #ff00ff;
    -webkit-animation: spin 1.5s linear infinite;
    animation: spin 1.5s linear infinite;
  }
  @-webkit-keyframes spin {
    0% {
      -webkit-transform: rotate(0deg);
      -ms-transform: rotate(0deg);
      transform: rotate(0deg);
    }
    100% {
      -webkit-transform: rotate(360deg);
      -ms-transform: rotate(360deg);
      transform: rotate(360deg);
    }
  }
  @keyframes spin {
    0% {
      -webkit-transform: rotate(0deg);
      -ms-transform: rotate(0deg);
      transform: rotate(0deg);
    }
    100% {
      -webkit-transform: rotate(360deg);
      -ms-transform: rotate(360deg);
      transform: rotate(360deg);
    }
  }
</style>
