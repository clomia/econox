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
    border-radius: 60px;
    overflow: hidden;
    width: 100%;
    position: fixed;
    left: 50%;
    max-width: 50%;
    top: 50%;
    transform: translate3d(-50%, -50%, 0);
  }

  .bar {
    background: rgba(0, 0, 0, 0.075);
    display: block;
  }

  .progress {
    background: #75b800;
    color: #fff;
    padding: 5px;
    transition: width 0.5s ease;
  }
</style>
