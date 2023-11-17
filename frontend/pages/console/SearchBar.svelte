<script lang="ts">
    import axios from "axios";
    import Swal from "sweetalert2";
    import { onMount } from "svelte";
    import { fade } from "svelte/transition";
    import { Packets, News, CountryCodeMap, PacketInfo } from "../../modules/state";
    import Magnifier from "../../assets/icon/Magnifier.svelte";
    import PlusIcon from "../../assets/icon/PlusIcon.svelte";
    import MinusIcon from "../../assets/icon/MinusIcon.svelte";
    import DotLoader from "../../assets/animation/DotLoader.svelte";
    import ToggleArrow from "../../assets/icon/ToggleArrow.svelte";
    import TextLoader from "../../assets/animation/TextLoader.svelte";
    import { api } from "../../modules/request";
    import { Text, Lang, UnivariateElements } from "../../modules/state";
    import { defaultSwalStyle, format } from "../../modules/functions";
    import CloseButton from "../../components/CloseButton.svelte";
    import type { ElementType, RespPacketType } from "../../modules/state";

    let univariateRequests: any = {};
    /**
     * 단변량 요소 추가 요청을 저장합니다.
     */
    const univariateAppend = (element: ElementType) => {
        $UnivariateElements = [
            {
                code: element.code,
                code_type: element.type,
                name: element.name,
                note: element.note,
                update_time: new Date().toISOString(),
            },
            ...$UnivariateElements,
        ];
        univariateRequests[`${element.code}|${element.type}`] = "append";
    };
    /**
     * 단변량 요소 삭제 요청을 저장합니다.
     */
    const univariateDelete = (element: ElementType) => {
        const target = $UnivariateElements.find(
            (ele) => ele.code === element.code && ele.code_type === element.type
        );
        if (!target) {
            throw new Error("Element does not exists");
        }
        $UnivariateElements = $UnivariateElements.filter((ele) => ele !== target);
        univariateRequests[`${element.code}|${element.type}`] = "delete";
    };
    /**
     * 창이 닫히면 단변량 요소 추가/삭제 요청을 한번에 처리합니다.
     */
    const closePacketInfo = () => {
        const requests = { ...univariateRequests }; // 모인 요청데이터를 함수 내부로 복사
        univariateRequests = {}; // 요청데이터 초기화 -> 상태를 바로 초기화해줘야 함
        packetInfoOn = false; // 창 닫기
        // 비동기적으로 모든 요청을 API로 전송
        Promise.all(
            Object.entries(requests).map(([key, action]) => {
                const [code, code_type] = key.split("|");
                if (action === "append") {
                    return api.member.post("/feature/user/element", {}, { params: { code, code_type } });
                } else if (action === "delete") {
                    return api.member.delete("/feature/user/element", { params: { code, code_type } });
                }
            })
        );
    };

    let inputText = "";
    const createPacket = async () => {
        const query = inputText.trim();
        if (!query) {
            return;
        }
        // 동일한 query 값을 가진 패킷이 Packets 내에 있는지 확인
        if ($Packets.find((p) => p.query === query)) {
            return await Swal.fire({
                ...defaultSwalStyle,
                confirmButtonText: $Text.Ok,
                icon: "info",
                showDenyButton: false,
                title: $Text.SearchRequestAlreadyExist,
            });
        }
        if ($Packets[3]?.loading) {
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
        $Packets = [initialPacket, ...$Packets.slice(0, 3)];
        try {
            const resp = await api.member.get("/data/elements", { params: { query, lang: $Lang } });
            const updatedPacket = { query, loading: false, resp: resp.data };
            const index = $Packets.findIndex((p) => p.query === query && p.loading);
            if (index !== -1) {
                $Packets[index] = updatedPacket; // 패킷 로딩은 여기서 종료됨
            }

            // symbols 타입만 뉴스 가져올 수 있음
            const loadingFrame = Object.fromEntries(resp.data.symbols.map((ele: any) => [ele.code, null]));
            $News = { ...$News, ...loadingFrame }; // 값이 null인 경우 로딩중

            const newsData = await Promise.all(
                resp.data.symbols.map(async (ele: any) => {
                    try {
                        const resp = await api.member.get("/data/news", {
                            params: { symbol: ele.code, lang: $Lang },
                        });
                        const newsContents = resp.data.contents.map((content: any) => {
                            return { ...content, isOpen: false };
                        });
                        return [resp.data.symbol.code, newsContents];
                    } catch {
                        return ["blank", null];
                    }
                })
            ); // 값이 []인 경우 뉴스 없음
            $News = { ...$News, ...Object.fromEntries(newsData) };
        } catch {
            $Packets = $Packets.filter((p) => p.query !== query);
            return await Swal.fire({
                ...defaultSwalStyle,
                confirmButtonText: $Text.Ok,
                icon: "info",
                showDenyButton: false,
                title: format($Text.f_DataSearchError, { query }),
            });
        }
    };

    let selectedElement: ElementType;
    let packetInfoOn = false;
    const onPacketInfo = async (query: string, resp: RespPacketType) => {
        const countries = resp["countries"].map((obj) => {
            obj.type = "country";
            return obj;
        });
        const symbols = resp["symbols"].map((obj) => {
            obj.type = "symbol";
            return obj;
        });
        $PacketInfo = { query, resp, elements: [...countries, ...symbols] };
        selectedElement = $PacketInfo.elements[0];
        packetInfoOn = true;
    };
    const noResultAlert = async () => {
        return await Swal.fire({
            ...defaultSwalStyle,
            confirmButtonText: $Text.Ok,
            icon: "info",
            showDenyButton: false,
            title: $Text.NoSearchResult,
        });
    };
    /**
     * 2023-09-26T07:04:20.000Z 형식의 문자열을 받아 브라우저 시간대에 맞는 연.월.일 및 시:분:초 문자열 반환
     */
    const timeString = (str: string) => {
        const date = new Date(str);
        const year = date.getFullYear();
        const month = (date.getMonth() + 1).toString().padStart(2, "0");
        const day = date.getDate().toString().padStart(2, "0");
        const hours = date.getHours().toString().padStart(2, "0");
        const minutes = date.getMinutes().toString().padStart(2, "0");
        const seconds = date.getSeconds().toString().padStart(2, "0");

        return `${year}.${month}.${day} ${hours}:${minutes}:${seconds}`;
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
        {#each $Packets as { query, loading, resp }}
            <div class="packet">
                <div class="packet__query"><span>{query}</span></div>
                {#if loading}
                    <div class="packet__loader"><DotLoader /></div>
                {:else if resp.symbols.length === 0 && resp.countries.length === 0}
                    <button class="packet__result" on:click={noResultAlert}>
                        <img in:fade src="static/img/nofile.png" alt="result" height="25px" />
                    </button>
                {:else}
                    <button class="packet__result" on:click={() => onPacketInfo(query, resp)}>
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
            <button class="packet-info__close-button" on:click={closePacketInfo}>
                <CloseButton />
            </button>
            <div class="packet-info__magnifier">
                <Magnifier size="1.3rem" />
            </div>
            <div class="packet-info__query">
                <div class="packet-info__query__text">{$PacketInfo.query}</div>
            </div>
            <div class="packet-info__list">
                {#each $PacketInfo.elements as element}
                    {@const isInUnivariateList = !!$UnivariateElements.find(
                        (ele) => ele.code === element.code && ele.code_type === element.type
                    )}
                    <button
                        class="packet-info__list__ele"
                        on:click={() => (selectedElement = element)}
                        class:selected={selectedElement === element}
                    >
                        <div class="packet-info__list__ele__code">{element.code}</div>
                        <div class="packet-info__list__ele__name">
                            {element.name}
                            {#if element.type === "country" && $CountryCodeMap}
                                {@const code = $CountryCodeMap[element.code].toLowerCase()}
                                <img
                                    src={`https://flagcdn.com/w40/${code}.png`}
                                    alt={element.name}
                                    width="30px"
                                />
                            {/if}
                        </div>
                        <button
                            class="packet-info__list__ele__add-btn"
                            on:click={() => {
                                isInUnivariateList ? univariateDelete(element) : univariateAppend(element);
                            }}
                        >
                            {#if isInUnivariateList}
                                <MinusIcon size={1.2} />
                            {:else}
                                <PlusIcon size={1.2} />
                            {/if}
                        </button>
                    </button>
                {/each}
            </div>
            <div class="packet-info__repr">
                <div class="packet-info__repr__name">{selectedElement.name}</div>
                <div class="packet-info__repr__note">{selectedElement.note}</div>
            </div>
            <div class="packet-info__news">
                <div class="packet-info__news__icon">
                    <img src="static/img/megaphone.png" width="20px" alt="Megaphone" />
                    <div class="packet-info__news__icon__text">News</div>
                </div>
                {#if selectedElement.type === "symbol"}
                    {#if !$News[selectedElement.code]}
                        <div class="packet-info__news__loading"><TextLoader /></div>
                    {:else if $News[selectedElement.code].length === 0}
                        <div class="packet-info__news__null">{$Text.ElementNewsNotFound}</div>
                    {:else}
                        {#each $News[selectedElement.code] as newsElement}
                            <div class="packet-info__news__ele">
                                <button
                                    class="packet-info__news__ele__head"
                                    on:click={() => (newsElement.isOpen = true)}
                                    class:news-ele-no-hover={newsElement.isOpen}
                                >
                                    <div
                                        class="packet-info__news__ele__head__title"
                                        class:opened-news-title={newsElement.isOpen}
                                    >
                                        {newsElement.title}
                                    </div>
                                    <div class="packet-info__news__ele__head__date">
                                        {timeString(newsElement.date)}
                                    </div>
                                </button>
                                {#if newsElement.isOpen}
                                    <div class="packet-info__news__ele__body">
                                        <div class="packet-info__news__ele__body__content">
                                            {newsElement.content}
                                        </div>
                                        <div class="packet-info__news__ele__body__buttons">
                                            <div style="width: 25px;" />
                                            <button
                                                class="packet-info__news__ele__body__buttons__close"
                                                on:click={() => (newsElement.isOpen = false)}
                                            >
                                                <ToggleArrow size={0.6} />
                                            </button>
                                            <a
                                                href={newsElement.src}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                            >
                                                <div class="packet-info__news__ele__body__buttons__href">
                                                    <img
                                                        src="static/img/link.png"
                                                        alt={newsElement.src}
                                                        width="25px"
                                                    />
                                                </div>
                                            </a>
                                        </div>
                                    </div>
                                {/if}
                            </div>
                        {/each}
                    {/if}
                {:else}
                    <div class="packet-info__news__null">{$Text.ElementNewsNotSupported}</div>
                {/if}
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
        opacity: 0.5;
        transition: opacity 100ms ease-out;
    }
    .search-btn:hover {
        opacity: 1;
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

    .opened-news-title {
        font-size: 1.1rem;
    }
    .packet-info__news {
        margin: 0 3rem;
        padding: 1rem 0;
    }
    .packet-info__news__icon {
        display: flex;
        justify-content: center;
        opacity: 0.8;
        margin-bottom: 1rem;
    }
    .packet-info__news__icon__text {
        color: white;
        margin-left: 0.5rem;
        font-size: 1.1rem;
    }
    .packet-info__news__loading {
        display: flex;
        justify-content: center;
        align-items: center;
        transform: scale(0.6);
        margin-top: -2rem;
        margin-bottom: 1.5rem;
    }
    .packet-info__news__null {
        text-align: center;
        color: var(--white);
    }
    .packet-info__news__ele {
        border-bottom: thin solid rgba(255, 255, 255, 0.2);
        color: var(--white);
    }
    .packet-info__news__ele__head {
        width: 100%;
        display: flex;
        flex-direction: column;
        color: var(--white);
        padding: 0.7rem;
    }
    .packet-info__news__ele__head:hover {
        cursor: pointer;
        background-color: rgba(255, 255, 255, 0.15);
    }
    .news-ele-no-hover {
        cursor: default !important;
        background-color: transparent !important;
    }
    .packet-info__news__ele__head__title {
        text-align: start;
    }
    .packet-info__news__ele__head__date {
        width: 100%;
        text-align: end;
        color: rgba(255, 255, 255, 0.4);
        margin-top: 0.35rem;
    }
    .packet-info__news__ele__body {
        padding: 0.7rem;
        padding-top: 0;
    }
    .packet-info__news__ele__body__buttons {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 0.4rem;
    }
    .packet-info__news__ele__body__buttons__close {
        opacity: 0.4;
        transform: rotateZ(180deg);
    }
    .packet-info__news__ele__body__buttons__href {
        opacity: 0.4;
    }
    .packet-info__news__ele__body__buttons__close:hover,
    .packet-info__news__ele__body__buttons__href:hover {
        cursor: pointer;
        opacity: 1;
    }

    .packet-info {
        width: 44rem;
        min-height: 31rem;
        margin-top: 18.5rem;
        background: var(--widget-background);
        border-radius: 0.3rem;
        border: thin solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 0 10rem 0.2rem rgba(0, 0, 0, 0.5);
        position: relative;
        padding-bottom: 2rem;
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
        color: var(--white);
        font-size: 1.3rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .packet-info__list {
        display: flex;
        flex-direction: column;
        margin: 0 3rem;
        margin-top: 2rem;
    }
    .packet-info__list__ele {
        display: flex;
        align-items: center;
        padding: 0.5rem 0;
        border-radius: 0.35rem;
        border: thin solid rgba(255, 255, 255, 0);
        position: relative;
    }
    .packet-info__list__ele.selected {
        border-color: rgba(255, 255, 255, 0.2);
    }
    .packet-info__list__ele:hover {
        background-color: rgba(255, 255, 255, 0.07);
        cursor: pointer;
    }
    .packet-info__list__ele__code {
        padding: 0.2rem 0.4rem;
        border-radius: 0.2rem;
        margin: 0 0.5rem;
        color: var(--white);
        background-color: rgba(255, 255, 255, 0.2);
    }
    .packet-info__list__ele__name {
        color: var(--white);
    }
    .packet-info__list__ele__add-btn {
        width: 2rem;
        height: 2rem;
        position: absolute;
        right: 0.5rem;
        border-radius: 0.3rem;
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: 0.7;
    }
    .packet-info__list__ele__add-btn:hover {
        background-color: rgba(255, 255, 255, 0.1);
        cursor: pointer;
        opacity: 1;
    }

    .packet-info__repr {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin: 0 3rem;
        margin-top: 1rem;
        border-top: thin solid rgba(255, 255, 255, 0.1);
        border-bottom: thin solid rgba(255, 255, 255, 0.1);
        padding: 0.7rem 0;
        text-align: justify;
        text-justify: inter-word;
    }
    .packet-info__repr__name {
        color: var(--white);
        font-size: 1.1rem;
    }
    .packet-info__repr__note {
        color: var(--white);
        padding: 0 1rem;
        padding-top: 1rem;
        white-space: pre-line;
    }
</style>
