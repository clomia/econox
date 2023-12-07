<script lang="ts">
  import { navigate } from "svelte-routing";
  import { UserInfo, Text } from "../modules/state";
  import Profile from "../assets/icon/Profile.svelte";
</script>

<section>
  <button>{$Text.Econox}</button>
  <button on:click={() => navigate("/console")}>{$Text.Console}</button>
  <button>{$Text.FeatureHub}</button>
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
    padding: 3rem 0;
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
