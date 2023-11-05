<script lang="ts">
    import Elements from "./Elements.svelte";
    import Factors from "./Factors.svelte";
</script>

<main>
    <div class="selector">
        <div class="selector__window"><Elements /></div>
        <div class="selector__window"><Factors /></div>
    </div>
    <div id="Note" />
    <div id="Chart" />
</main>

<style>
    main {
        width: 44rem;
        border: thin solid rgba(255, 255, 255, 0.2);
        border-radius: 0.5rem;
        box-shadow: 0 0 2rem 0.1rem rgba(0, 0, 0, 0.5);
    }
    .selector {
        display: flex;
    }
    .selector__window {
        width: 50%;
        min-height: 10rem;
    }
    #Note {
        height: 10rem;
        border-top: thin solid var(--border-white);
        border-bottom: thin solid var(--border-white);
    }
    #Chart {
        height: 30rem;
    }
</style>
