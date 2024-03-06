<script lang="ts">
  export let text: string = "텍스트 미할당";
  export let color: string = "rgb(230, 230, 230)";
</script>

<div class="btn" style="color: {color}; border-color: {color};">{text}</div>

<style>
  .btn {
    font-size: 1.2rem;
    padding: 0.7rem 2rem;
    border: 1px solid;
    position: relative;
    overflow: hidden;
  }

  .btn:hover {
    box-shadow: 1px 1px 25px 10px rgba(146, 148, 248, 0.4);
  }

  @keyframes slideAnimation {
    0% {
      left: -100%;
    }
    50% {
      left: 100%;
    }
    100% {
      left: 100%;
    }
  }

  .btn:before {
    content: "";
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(
      120deg,
      transparent,
      rgba(146, 148, 248, 0.4),
      transparent
    );
    animation: slideAnimation 2.5s ease-in-out infinite;
    transition: all 650ms;
  }
</style>
