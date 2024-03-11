<script lang="ts">
  import { onMount } from "svelte";
  import { verify } from "../../modules/functions";
  import { auth } from "../../modules/state";
  import Login from "./Login.svelte";
  import Signup from "./signup/Index.svelte";
  import LoginSignupToggle from "./LoginSignupToggle.svelte";

  verify({ conds: { login: false }, failRedirect: "/account" });
  const Toggle = auth.Toggle;

  onMount(() => {
    // URL에 #로 기본 상태를 지정해줄수도 있다
    if (location.hash === "#login") {
      $Toggle.login = true;
      $Toggle.signup = false;
    } else if (location.hash === "#signup") {
      $Toggle.login = false;
      $Toggle.signup = true;
    } else {
      location.hash = "#login";
    }
  });
</script>

<div class="ground">
  <div class="ground__window">
    <LoginSignupToggle />
    <section>
      {#if $Toggle.login}
        <Login />
      {:else}
        <Signup />
      {/if}
    </section>
  </div>
</div>

<style>
  .ground {
    display: flex;
    justify-content: center;
    align-items: start;
    margin-top: 2rem;
    height: 45rem;
  }
  .ground__window {
    width: 34rem;
    padding: 3rem 4rem;
    border-radius: 0.6rem;
    border: thin solid rgba(255, 255, 255, 0.2);
    background: var(--widget-background);
    box-shadow: 0 0 2rem 0.1rem rgba(0, 0, 0, 0.5);
  }
</style>
