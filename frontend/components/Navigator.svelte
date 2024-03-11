<script lang="ts">
  import { navigate } from "svelte-routing";
  import { swal } from "../modules/functions";
  import { UserInfo, Text } from "../modules/state";
  import Profile from "../assets/icon/Profile.svelte";

  export let url: string;
  $: isIntroPage = url === "/";
  let hide = isIntroPage && window.innerWidth < 770;
  window.addEventListener("resize", () => {
    hide = isIntroPage && window.innerWidth < 770;
  });

  const navConsole = async () => {
    if ($UserInfo.id) {
      navigate("/console");
    } else {
      await swal($Text.LoginRequired, "25rem");
      navigate("/auth");
    }
  };
  const navFeatureHub = async () => {
    await swal($Text.ComingSoon, "25rem");
  };
</script>

<section style={hide ? "display: none;" : ""}>
  <button on:click={() => navigate("/")}>Econox</button>
  <button on:click={navConsole}>{$Text.Console}</button>
  <button on:click={navFeatureHub}>{$Text.FeatureHub}</button>
  {#if $UserInfo.id}
    <button on:click={() => navigate("/account")}>
      <div class="profile-icon"><Profile /></div>
      <div class="username">{$UserInfo.name}</div>
    </button>
  {:else}
    <button on:click={() => navigate("/auth")}>{$Text.SignInOut}</button>
  {/if}
</section>

<style>
  .profile-icon {
    width: 1.6rem;
    height: 1.6rem;
    position: absolute;
    left: 0.4rem;
    opacity: 0.65;
  }
  .username {
    margin-left: 1rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    width: 6rem;
  }
  section {
    display: flex;
    justify-content: center;
    padding: 3rem 2rem;
    white-space: nowrap;
  }

  section button {
    display: flex;
    justify-content: center;
    align-items: center;
    margin: 0 0.7rem;
    width: 10rem;
    height: 2.4rem;
    color: var(--white);
    border: thin solid var(--border-white);
    border-radius: 2rem;
    position: relative;
    box-shadow: 0 0 2rem 0.1rem rgba(0, 0, 0, 0.3);
  }

  section button:hover {
    background-color: rgba(255, 255, 255, 0.16);
    cursor: pointer;
  }
</style>
