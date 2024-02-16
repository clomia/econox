<script lang="ts">
  import { Text } from "../../../../modules/state";
  import FullScreenIcon from "../../../../assets/icon/FullScreenIcon.svelte";
  import LinkIcon from "../../../../assets/icon/LinkIcon.svelte";
</script>

<main>
  <div></div>
  <button class="share">
    <LinkIcon size="1rem" />
    <div class="share__text">{$Text.ShareDataGroup}</div>
  </button>
  <button class="fullscreen"><FullScreenIcon /></button>
</main>

<style>
  main {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .share {
    margin-right: 1rem;
    display: flex;
    align-items: center;
  }
  .share__text {
    color: white;
    margin-left: 0.5rem;
  }
  button {
    opacity: 0.5;
  }
  button:hover {
    cursor: pointer;
    opacity: 1;
  }
  main {
    padding: 1rem;
    padding-bottom: 0;
  }
</style>
