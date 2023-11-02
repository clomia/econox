<script lang="ts">
    import Elements from "./Elements.svelte";
</script>

<main>
    <div class="selector">
        <Elements />
        <div id="Factors" />
    </div>
    <div id="Note" />
    <div id="Chart" />
</main>

<style>
    main {
        width: 44rem;
        border: thin solid var(--border-white);
    }
    .selector {
        display: flex;
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
