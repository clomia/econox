<script lang="ts">
  export let href: string = "/";
  export let content: string = "Discover the project";
  export let color: string = "#FFFFFF";
</script>

<main class="content" data-form-type="card">
  <a
    {href}
    target="_blank"
    rel="noopener noreferrer"
    class="btn"
    style="color: {color};"
  >
    <span class="btn__circle" style="color: {color};"></span>
    <span class="btn__white-circle" style="color: {color};">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        id="icon-arrow-right"
        viewBox="0 0 21 12"
      >
        <path
          d="M17.104 5.072l-4.138-4.014L14.056 0l6 5.82-6 5.82-1.09-1.057 4.138-4.014H0V5.072h17.104z"
        ></path>
      </svg>
    </span>
    <span class="btn__text">{content}</span>
  </a>
</main>

<style>
  .btn {
    display: inline-block;
    padding: 32px;
    position: relative;
    letter-spacing: 1px;
  }
  .btn__circle,
  .btn__text,
  .btn__white-circle {
    position: absolute;
  }
  .btn__circle {
    top: 35%;
    left: 15%;
    height: 30%;
    width: 30%;
    border-radius: 100%;
    box-shadow: 0 0 1px 1px #fff;
    transition: 0.3s linear;
  }
  .btn__white-circle {
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%) scale(0);
    width: 56px;
    height: 56px;
    border-radius: 100%;
    background: #ffffff;
    display: flex;
    transition: 0.3s ease-in-out;
  }
  .btn__white-circle svg {
    width: 24px;
    height: 24px;
    margin: auto;
  }
  .btn__text {
    top: 50%;
    transform: translateY(-50%);
    white-space: nowrap;
    z-index: 2;
    padding: 24px 8px;
    font-size: 1.15rem;
    transition: 0.3s linear;
  }
  .btn:hover .btn__circle {
    transform: scale(0);
  }
  .btn:hover .btn__white-circle {
    transform: translate(-25%, -50%) scale(0.7);
  }
  .btn:hover .btn__text {
    transform: translate(40px, -50%);
  }

  .content {
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    transition: 0.3s linear;
  }
  .content:hover {
    transform: translateX(-30px);
  }
</style>
