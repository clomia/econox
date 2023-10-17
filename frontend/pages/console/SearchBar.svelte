<script>
    import Magnifier from "../../assets/icon/Magnifier.svelte";
    import { Text } from "../../modules/state";
</script>

<main>
    <div class="magnifier"><Magnifier /></div>
    <input type="text" name="search" placeholder={$Text.SearchBar_Placeholder} />
</main>

<style>
    main {
        display: flex;
        align-items: center;
        width: 44rem;
        height: 2.6rem;
        border-radius: 1.5rem;
        border: thin solid var(--border-white);
        box-shadow: 0 0 2rem 0.1rem rgba(0, 0, 0, 0.2);
        transition: border-color 100ms ease-in-out;
    }
    main:hover {
        border-color: rgba(255, 255, 255, 0.5);
        box-shadow: 0 0 0.5rem 0.1rem rgba(255, 255, 255, 0.1);
    }
    .magnifier {
        margin-left: 1.4rem;
        margin-top: 0.2rem;
        margin-right: 0.8rem;
    }
    main > input {
        width: 100%;
        color: var(--white);
        margin-right: 1.4rem;
    }
</style>
