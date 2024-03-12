<script lang="ts">
  import SvelteTypedJs from "svelte-typed-js";

  import { Text, UserInfo } from "../modules/state";
  import { navigate } from "../modules/functions";
  import TerminalArrow from "../assets/icon/TerminalArrow.svelte";
  import ReflectiveButton from "../components/ReflectiveButton.svelte";

  let color = "rgb(170, 170, 170)";

  const buttonClick = () => {
    if ($UserInfo.id) {
      navigate("/console");
    } else {
      navigate("/");
    }
  };
</script>

<main>
  <div class="code" style="color: {color};">404</div>
  <section style="color: {color};">
    <TerminalArrow size="2.5rem" {color} />
    <SvelteTypedJs
      strings={["Page Not Found"]}
      typeSpeed={30}
      showCursor={true}
      cursorChar="_"
    >
      <span class="typing" />
    </SvelteTypedJs>
  </section>
  <button on:click={buttonClick}>
    <ReflectiveButton
      text={$UserInfo.id ? $Text.GoToConsole : $Text.GoToHome}
      {color}
    />
  </button>
</main>

<style>
  main {
    width: calc(100vw - 0.4rem);
    height: 65vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }
  .code {
    font-size: 6rem;
  }
  section {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    padding: 0 2rem;
    overflow-x: hidden;
    font-size: 3rem;
    fill: red;
  }
  span {
    margin-left: 0.9rem;
    white-space: nowrap;
  }
  button {
    margin-top: 3.5rem;
  }
  button:hover {
    cursor: pointer;
  }
</style>
