<script lang="ts">
  import { createEventDispatcher } from "svelte";
  import {
    UnivariateElementSelected,
    UnivariateFactorSelected,
  } from "../../../../modules/state";
  export let normalized: boolean;

  const dispatch = createEventDispatcher();
</script>

<div>파일 포멧 선택!</div>
<div>{normalized}</div>

<button on:click={() => dispatch("close")}>Close</button>
