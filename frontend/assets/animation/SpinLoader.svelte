<script>
  export let size = 1;
</script>

<div style="transform: scale({size})">
  <span class="loader"></span>
</div>

<style>
  .loader {
    width: 48px;
    height: 48px;
    border: 5px solid rgba(255, 255, 255, 0.6);
    border-bottom-color: transparent;
    border-radius: 50%;
    display: inline-block;
    box-sizing: border-box;
    animation: rotation 500ms linear infinite;
  }

  @keyframes rotation {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }
</style>
