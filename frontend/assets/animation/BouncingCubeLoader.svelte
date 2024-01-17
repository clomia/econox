<script>
  export let borderColor = "#40533e";
  export let backgroundColor = "#ff00f7";
</script>

<main>
  <div class="scene">
    <div class="cube-wrapper">
      <div class="cube">
        <div class="cube-faces">
          <div
            class="cube-face shadow"
            style="background-color: {backgroundColor}; border: solid 1px {borderColor};"
          ></div>
          <div
            class="cube-face bottom"
            style="background-color: {backgroundColor}; border: solid 1px {borderColor};"
          ></div>
          <div
            class="cube-face top"
            style="background-color: {backgroundColor}; border: solid 1px {borderColor};"
          ></div>
          <div
            class="cube-face left"
            style="background-color: {backgroundColor}; border: solid 1px {borderColor};"
          ></div>
          <div
            class="cube-face right"
            style="background-color: {backgroundColor}; border: solid 1px {borderColor};"
          ></div>
          <div
            class="cube-face back"
            style="background-color: {backgroundColor}; border: solid 1px {borderColor};"
          ></div>
          <div
            class="cube-face front"
            style="background-color: {backgroundColor}; border: solid 1px {borderColor};"
          ></div>
        </div>
      </div>
    </div>
  </div>
</main>

<style>
  main {
    display: grid;
    place-items: center;
    position: relative;
  }

  .scene {
    position: relative;
    height: 220px;
    /* $size*2.75 */
    width: 220px;
    /* $size*2.75 */
    display: grid;
    place-items: center;
  }

  .cube-wrapper {
    transform-style: preserve-3d;
    animation: bouncing 2s infinite;
  }

  .cube {
    transform-style: preserve-3d;
    transform: rotateX(45deg) rotateZ(45deg);
    animation: rotation 2s infinite;
  }

  .cube-faces {
    transform-style: preserve-3d;
    height: 80px;
    /* $size */
    width: 80px;
    /* $size */
    position: relative;
    transform-origin: 0 0;
    transform: translateX(0) translateY(0) translateZ(-40px);
    /* -$size/2 */
  }

  .cube-face {
    position: absolute;
    inset: 0;
  }

  .cube-face.shadow {
    transform: translateZ(-80px);
    /* -$size */
    animation: bouncing-shadow 2s infinite;
  }

  .cube-face.top {
    transform: translateZ(80px);
    /* $size */
  }

  .cube-face.front {
    transform-origin: 0 50%;
    transform: rotateY(-90deg);
  }

  .cube-face.back {
    transform-origin: 0 50%;
    transform: rotateY(-90deg) translateZ(-80px);
    /* -$size */
  }

  .cube-face.right {
    transform-origin: 50% 0;
    transform: rotateX(-90deg) translateY(-80px);
    /* -$size */
  }

  .cube-face.left {
    transform-origin: 50% 0;
    transform: rotateX(-90deg) translateY(-80px) translateZ(80px);
    /* $size */
  }

  @keyframes rotation {
    0% {
      transform: rotateX(45deg) rotateY(0) rotateZ(45deg);
      animation-timing-function: cubic-bezier(0.17, 0.84, 0.44, 1);
    }

    50% {
      transform: rotateX(45deg) rotateY(0) rotateZ(225deg);
      /* 45deg + 360/2 */
      animation-timing-function: cubic-bezier(0.76, 0.05, 0.86, 0.06);
    }

    100% {
      transform: rotateX(45deg) rotateY(0) rotateZ(405deg);
      /* 45deg + 360 */
      animation-timing-function: cubic-bezier(0.17, 0.84, 0.44, 1);
    }
  }

  @keyframes bouncing {
    0% {
      transform: translateY(-40px);
      /* -$size*.5 */
      animation-timing-function: cubic-bezier(0.76, 0.05, 0.86, 0.06);
    }

    45% {
      transform: translateY(40px);
      /* $size*.5 */
      animation-timing-function: cubic-bezier(0.23, 1, 0.32, 1);
    }

    100% {
      transform: translateY(-40px);
      /* -$size*.5 */
      animation-timing-function: cubic-bezier(0.76, 0.05, 0.86, 0.06);
    }
  }

  @keyframes bouncing-shadow {
    0% {
      transform: translateZ(-80px) scale(1.3);
      /* -$size */
      animation-timing-function: cubic-bezier(0.76, 0.05, 0.86, 0.06);
      opacity: 0.2;
    }

    45% {
      transform: translateZ(0);
      animation-timing-function: cubic-bezier(0.23, 1, 0.32, 1);
      opacity: 0.8;
    }

    100% {
      transform: translateZ(-80px) scale(1.3);
      /* -$size */
      animation-timing-function: cubic-bezier(0.76, 0.05, 0.86, 0.06);
      opacity: 0.2;
    }
  }
</style>
