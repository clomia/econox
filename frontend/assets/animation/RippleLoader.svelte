<script>
  export let size = 1;
</script>

<div class="wrap" style="transform: scale({size});">
  <div class="spinner" />
</div>

<style>
  /* Converted CSS from SCSS for Spinner #3 */
  .spinner {
    position: relative;
    width: 62.5px; /* $basic-spinner-dimensions */
    height: 62.5px; /* $basic-spinner-dimensions */
  }

  .spinner:before,
  .spinner:after {
    content: "";
    display: block;
    position: absolute;
    border-width: 2px; /* $border-width */
    border-style: solid;
    border-radius: 50%;
  }

  .spinner:before {
    width: 58.5px; /* $main-spinner-dimensions */
    height: 58.5px; /* $main-spinner-dimensions */
    border-color: white; /* $basic-dark-color */
    top: 0px;
    left: 0px;
    animation: scale-2 1s linear 0s infinite;
  }

  .spinner:after {
    width: 58.5px; /* $main-spinner-dimensions */
    height: 58.5px; /* $main-spinner-dimensions */
    border-color: white; /* $basic-dark-color */
    top: 0;
    left: 0;
    opacity: 0;
    animation: scale-2 1s linear 0.5s infinite;
  }

  @keyframes scale-2 {
    0% {
      transform: scale(0);
      opacity: 0;
    }
    50% {
      transform: scale(0.7);
      opacity: 1;
    }
    100% {
      transform: scale(1);
      opacity: 0;
    }
  }
</style>
