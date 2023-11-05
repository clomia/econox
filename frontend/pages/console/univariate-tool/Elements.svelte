<script>
    import Magnifier from "../../../assets/icon/Magnifier.svelte";
</script>

<main>
    <div class="search"><Magnifier /> <input type="text" /></div>
</main>

<style>
    .search {
        display: flex;
        align-items: center;
        padding-left: 0.6rem;
        height: 2rem;
        border-bottom: thin solid rgba(255, 255, 255, 0.2);
    }
    .search input {
        height: 100%;
        margin-left: 0.6rem;
        width: 90%;
        color: var(--white);
    }
</style>
