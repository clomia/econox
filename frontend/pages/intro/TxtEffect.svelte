<script lang="ts">
  import SvelteTypedJs from "svelte-typed-js";
  import TerminalArrow from "../../assets/icon/TerminalArrow.svelte";

  export let txtArr: string[];
  export let color: string;
  export let size: string = "1rem";
</script>

<section style="font-size: {size}; color: {color};">
  <TerminalArrow size="1.3rem" {color} />
  <SvelteTypedJs
    strings={txtArr}
    loop="true"
    typeSpeed={30}
    backSpeed={20}
    smartBackspace={true}
    backDelay={900}
    showCursor={true}
    cursorChar="_"
  >
    <span class="typing" />
  </SvelteTypedJs>
</section>

<style>
  section {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    padding: 0 2rem;
    overflow-x: hidden;
  }
  span {
    margin-left: 0.9rem;
    white-space: nowrap;
  }
</style>
