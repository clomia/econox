<script lang="ts">
    import { api } from "../modules/request";

    async function test() {
        console.log(await api.member.get("/data/test"));
    }
</script>

<button style="border: 1px solid white; padding: 1rem; cursor:pointer;" on:click={test}>Test!</button>
<h1 style="color: var(--white);">This is landing page</h1>
