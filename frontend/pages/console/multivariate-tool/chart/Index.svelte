<script lang="ts">
  import Header from "./Header.svelte";
  import Menu from "./Menu.svelte";
  import Note from "./Note.svelte";
  import LineChart from "./render/Line.svelte";
  import RatioChart from "./render/Ratio.svelte";
</script>

<main>
  <div class="header"><Header /></div>
  여기는 차트...
  <div class="menu"><Menu /></div>
  <div class="note"><Note /></div>
</main>

<style>
  main {
    border-top: thin solid rgba(255, 255, 255, 0.2);
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    height: 5rem;
    color: white;
  }
</style>
