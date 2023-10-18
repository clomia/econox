<script lang="ts">
    import { writable } from "svelte/store";
    import { fade } from "svelte/transition";
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
        inputText = "";
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
        const initialPacket = { query, loading: true, resp: null };
        $packets = [initialPacket, ...$packets];
        const resp = await api.member.get("/data/elements", { params: { query, lang: $Lang } });
        const updatedPacket = { ...initialPacket, loading: false, resp: resp.data };
        const index = $packets.findIndex((p) => p.query === query && p.loading);
        $packets[index] = updatedPacket;
    };

    let packetBox: HTMLElement;
    const scrollLeft = () => {
        packetBox.scrollBy({ left: -400, behavior: "smooth" });
    };
    const scrollRight = () => {
        packetBox.scrollBy({ left: 400, behavior: "smooth" });
    };
    let buffer = 10; // 여유 값 설정
    let packetBoxIsOverflowing = false;
    $: if (packetBox && $packets.length) {
        packetBoxIsOverflowing =
            packetBox.scrollWidth > 0 && packetBox.scrollWidth > packetBox.clientWidth - buffer;
    }
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
        <button in:fade class="search-btn"
            ><img src="static/img/right-arrow.png" alt="search" height="25px" /></button
        >
    </form>
    <section>
        {#if packetBoxIsOverflowing} <button class="scroll-btn" on:click={scrollLeft}>←</button> {/if}
        <div class="packets" bind:this={packetBox}>
            {#each $packets as { query, resp }}
                <div class="packet">
                    <div class="packet__query"><span>{query}</span></div>
                    <div class="packet__loader"><DotLoader /></div>
                </div>
            {/each}
        </div>
        {#if packetBoxIsOverflowing} <button class="scroll-btn" on:click={scrollRight}>→</button> {/if}
    </section>
</main>

<style>
    main {
        width: 44rem;
    }
    section {
        width: 100%;
        display: flex;
        justify-content: space-between;
    }
    .scroll-btn {
        width: 3rem;
        background-color: blanchedalmond;
    }
    .packets {
        display: flex;
        flex-direction: row-reverse;
        width: 100%;
        height: 4.3rem;
        overflow: auto;
        white-space: nowrap;
    }
    .packet {
        width: 8rem;
        height: 100%;
        margin: 0 0.7rem;
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
            box-shadow: 0 0 0.5rem 0.1rem rgba(255, 255, 255, 0.05);
        }
        50% {
            box-shadow: 0 0 0.5rem 0.1rem rgba(255, 255, 255, 0.2);
        }
    }
    .packet__loader {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 2rem;
        width: 100%;
        border: thin solid rgba(255, 255, 255, 0.5);
        border-radius: 1rem;
        animation: shadowPulse 1400ms infinite;
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
