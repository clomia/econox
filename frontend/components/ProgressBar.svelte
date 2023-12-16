<script>
  export let progress = 0; // 진행률은 0에서 1 사이의 값
</script>

<div class="progress-bar">
  <div class="bar">
    <div class="progress" style="width: {progress * 100}%"></div>
  </div>
</div>

<style>
  .progress-bar {
    border-radius: 2rem;
    overflow: hidden;
    width: 100%;
    max-width: 100%;
  }

  .bar {
    background: rgba(0, 0, 0, 0.3);
  }

  .progress {
    background: rgba(255, 255, 255, 0.3);
    padding: 0.1rem;
    transition: width 0.5s ease;
  }
</style>
