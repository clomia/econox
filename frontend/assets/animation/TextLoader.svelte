<main>
  <h1>
    <span class="let1">l</span>
    <span class="let2">o</span>
    <span class="let3">a</span>
    <span class="let4">d</span>
    <span class="let5">i</span>
    <span class="let6">n</span>
    <span class="let7">g</span>
  </h1>
</main>

<style>
  main {
    height: 100%;
    width: 100%;
    margin: 0;
    padding: 0;
    font-size: 100%;
    text-align: center;
    line-height: 1;
  }

  h1 {
    margin: 0;
    padding: 0;
    font-family:
      ‘Arial Narrow’,
      sans-serif;
    font-weight: 100;
    font-size: 3rem;
    color: var(--white);
  }

  span {
    position: relative;
    top: 0.63rem;
    display: inline-block;
    text-transform: uppercase;
    opacity: 0;
    transform: rotateX(-90deg);
  }

  .let1 {
    animation: drop 1.2s ease-in-out infinite;
    animation-delay: 0.2s;
  }

  .let2 {
    animation: drop 1.2s ease-in-out infinite;
    animation-delay: 0.3s;
  }

  .let3 {
    animation: drop 1.2s ease-in-out infinite;
    animation-delay: 0.4s;
  }

  .let4 {
    animation: drop 1.2s ease-in-out infinite;
    animation-delay: 0.5s;
  }

  .let5 {
    animation: drop 1.2s ease-in-out infinite;
    animation-delay: 0.6s;
  }

  .let6 {
    animation: drop 1.2s ease-in-out infinite;
    animation-delay: 0.7s;
  }

  .let7 {
    animation: drop 1.2s ease-in-out infinite;
    animation-delay: 0.8s;
  }

  @keyframes drop {
    10% {
      opacity: 0.5;
    }
    20% {
      opacity: 1;
      top: 3.78rem;
      transform: rotateX(-360deg);
    }
    80% {
      opacity: 1;
      top: 3.78rem;
      transform: rotateX(-360deg);
    }
    90% {
      opacity: 0.5;
    }
    100% {
      opacity: 0;
      top: 6.94rem;
    }
  }
</style>
