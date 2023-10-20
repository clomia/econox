<script lang="ts">
    import { fade } from "svelte/transition";
    import { writable } from "svelte/store";
    import Swal from "sweetalert2";
    import Magnifier from "../../assets/icon/Magnifier.svelte";
    import DotLoader from "../../assets/animation/DotLoader.svelte";
    import { api } from "../../modules/request";
    import { Text, Lang } from "../../modules/state";
    import { defaultSwalStyle, format } from "../../modules/functions";
    import CloseButton from "../../components/CloseButton.svelte";

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
        try {
            const resp = await api.member.get("/data/elements", { params: { query, lang: $Lang } });
            const updatedPacket = { ...initialPacket, loading: false, resp: resp.data };
            const index = $packets.findIndex((p) => p.query === query && p.loading);
            if (index !== -1) {
                $packets[index] = updatedPacket;
            }
        } catch {
            $packets = $packets.filter((p) => p.query === query);
            return await Swal.fire({
                ...defaultSwalStyle,
                confirmButtonText: $Text.Ok,
                icon: "info",
                showDenyButton: false,
                title: format($Text.f_DataSearchError, { query }),
            });
        }
    };

    type PacketInfo = { query: string; resp: any };
    const packetInfo = writable<PacketInfo>({ query: "", resp: "" });
    let packetInfoOn = false;
    const onPacketInfo = (info: PacketInfo) => {
        $packetInfo = info;
        packetInfoOn = true;
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
                    <button
                        class="packet__result"
                        on:click={() => {
                            onPacketInfo({ query, resp });
                        }}
                    >
                        <img in:fade src="static/img/file.png" alt="result" height="25px" />
                    </button>
                {/if}
            </div>
        {/each}
    </section>
</main>

{#if packetInfoOn}
    <div id="membrane" />
    <div id="window">
        <section class="packet-info">
            <button class="packet-info__close-button" on:click={() => (packetInfoOn = false)}>
                <CloseButton />
            </button>
            <div class="packet-info__magnifier">
                <Magnifier size="1.3rem" color="rgba(255,255,255,0.3)" />
            </div>
            <div class="packet-info__query">
                <div class="packet-info__query__text">{$packetInfo.query}</div>
            </div>
        </section>
    </div>
{/if}

<style>
    main {
        width: 44rem;
    }
    #membrane {
        position: fixed;
        z-index: 1;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.2);
    }
    #window {
        position: absolute;
        top: 0;
        left: 0;
        display: flex;
        width: 100%;
        justify-content: center;
        z-index: 2;
    }
    .packet-info {
        width: 44rem;
        height: 31rem;
        margin-top: 18.5rem;
        background: var(--widget-background);
        border-radius: 0.3rem;
        border: thin solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 0 10rem 0.2rem rgba(0, 0, 0, 0.5);
        position: relative;
    }
    .packet-info__close-button {
        position: absolute;
        right: 1rem;
        top: 1rem;
    }
    .packet-info__magnifier {
        position: absolute;
        top: 1.8rem;
        left: 2rem;
    }
    .packet-info__query {
        margin-top: 1.8rem;
        padding: 0 6rem;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .packet-info__query__text {
        color: rgba(255, 255, 255, 0.6);
        font-size: 1.3rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .search-form {
        display: flex;
        align-items: center;
        width: 100%;
        height: 2.6rem;
        border-radius: 1.3rem;
        border: thin solid var(--border-white);
        box-shadow: 0 0 2rem 0.1rem rgba(0, 0, 0, 0.3);
        transition: border-color 150ms ease-out;
    }
    .search {
        width: 100%;
        height: 100%;
        padding-right: 0.7rem;
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
    /* pakcets */
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
        box-shadow: 0 0 2rem 0.1rem rgba(0, 0, 0, 0.3);
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
</style>
