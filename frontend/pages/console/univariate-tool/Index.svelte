<script lang="ts">
    import Elements from "./Elements.svelte";
    import Factors from "./Factors.svelte";
</script>

<main>
    <div class="element-selector"><Elements /></div>
    <div class="factor-selector"><Factors /></div>
</main>

<style>
    main {
        width: 44rem;
        border: thin solid rgba(255, 255, 255, 0.2);
        border-radius: 0.5rem;
        box-shadow: 0 0 2rem 0.1rem rgba(0, 0, 0, 0.5);
    }
</style>
