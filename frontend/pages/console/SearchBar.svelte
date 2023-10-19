<script lang="ts">
    import { fade } from "svelte/transition";
    import { writable } from "svelte/store";
    import Swal from "sweetalert2";
    import Magnifier from "../../assets/icon/Magnifier.svelte";
    import DotLoader from "../../assets/animation/DotLoader.svelte";
    import { api } from "../../modules/request";
    import { Text, Lang } from "../../modules/state";
    import { defaultSwalStyle } from "../../modules/functions";

    let inputText = "";
    const packets = writable<{ query: string; loading: boolean; resp: any }[]>([]);
    const createPacket = async () => {
        const query = inputText.trim();
        if (!query) {
            return;
        }
        // 동일한 query 값을 가진 패킷이 packets 내에 있는지 확인
        if ($packets.find((p) => p.query === query)) {
            return await Swal.fire({
                ...defaultSwalStyle,
                confirmButtonText: $Text.Ok,
                icon: "info",
                showDenyButton: false,
                title: $Text.SearchRequestAlreadyExist,
            });
        }
        if ($packets[3]?.loading) {
            // 가장 오래된 패킷이 대기중인 경우 새로운 패킷 추가를 막음
            return await Swal.fire({
                ...defaultSwalStyle,
                confirmButtonText: $Text.Ok,
                icon: "info",
                showDenyButton: false,
                title: $Text.SearchRequestRateTooFastMessage,
            });
        }
        inputText = "";
        const initialPacket = { query, loading: true, resp: null };
        $packets = [initialPacket, ...$packets.slice(0, 3)];
        const resp = await api.member.get("/data/elements", { params: { query, lang: $Lang } });
        const updatedPacket = { ...initialPacket, loading: false, resp: resp.data };
        const index = $packets.findIndex((p) => p.query === query && p.loading);
        if (index !== -1) {
            $packets[index] = updatedPacket;
        }
    };
</script>

<main>
    <form class="search-form" on:submit|preventDefault={createPacket}>
        <div class="magnifier"><Magnifier /></div>
        <input
            class="search"
            type="text"
            name="search"
            autocomplete="off"
            spellcheck="false"
            placeholder={$Text.SearchBar_Placeholder}
            bind:value={inputText}
        />
        <button class="search-btn">
            <img src="static/img/circle-arrow.png" alt="search" height="25px" />
        </button>
    </form>
    <section class="packets">
        {#each $packets as { query, loading, resp }}
            <div class="packet">
                <div class="packet__query"><span>{query}</span></div>
                {#if loading}
                    <div class="packet__loader"><DotLoader /></div>
                {:else}
                    <button class="packet__result">
                        <img in:fade src="static/img/file.png" alt="result" height="25px" />
                    </button>
                {/if}
            </div>
        {/each}
    </section>
</main>

<style>
    main {
        width: 44rem;
    }
    .packets {
        display: flex;
        justify-content: flex-end;
        height: 4.3rem;
        white-space: nowrap;
    }
    .packet {
        width: 9.95rem;
        height: 100%;
        margin-left: 1.4rem;
        flex-shrink: 0;
    }
    .packet__query {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 2.3rem;
        width: 100%;
        color: rgba(255, 255, 255, 0.3);
    }
    .packet__query > span {
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
        min-width: 0;
    }
    @keyframes shadowPulse {
        0%,
        100% {
            box-shadow: 0 0 0.6rem 0.1rem rgba(255, 255, 255, 0.05);
        }
        50% {
            box-shadow: 0 0 0.6rem 0.1rem rgba(255, 255, 255, 0.22);
        }
    }
    .packet__loader,
    .packet__result {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 2rem;
        width: 100%;
        border-radius: 1rem;
    }
    .packet__loader {
        border: thin solid rgba(255, 255, 255, 0.5);
        animation: shadowPulse 1400ms infinite;
    }
    .packet__result {
        border: thin solid white;
        opacity: 0.5;
    }
    .packet__result:hover {
        background-color: rgba(255, 255, 255, 0.2);
        cursor: pointer;
    }
    .search-form {
        display: flex;
        align-items: center;
        width: 100%;
        height: 2.6rem;
        border-radius: 1.3rem;
        border: thin solid var(--border-white);
        box-shadow: 0 0 2rem 0.1rem rgba(0, 0, 0, 0.2);
        transition: border-color 150ms ease-out;
    }
    .search {
        width: 100%;
        height: 100%;
        color: var(--white);
    }
    .magnifier {
        margin-left: 1.4rem;
        margin-top: 0.2rem;
        margin-right: 0.8rem;
    }
    .search-btn {
        width: 2.5rem;
        height: 100%;
        display: flex;
        align-items: center;
        opacity: 0.3;
        transition: opacity 100ms ease-out;
    }
    .search-btn:hover {
        opacity: 0.8;
        cursor: pointer;
    }
</style>
