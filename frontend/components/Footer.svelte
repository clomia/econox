<script lang="ts">
    import { onMount } from "svelte";
    import axios from "axios";
    import ISO6391 from "iso-639-1";
    import * as yaml from "js-yaml";
    import { generalObjectStore, settingObjectStore } from "../modules/storage";

    interface LangMap {
        [code: string]: string;
    }

    interface ContentsObject {
        base?: string;
        [key: string]: string | LangMap;
    }

    interface LangInfo {
        pin: string;
        langs: LangMap;
        contents: ContentsObject;
    }

    async function loadMultilingual(): Promise<LangInfo> {
        let multilingual: ContentsObject = await generalObjectStore.get(
            "multilingual"
        );
        let lang: string = await settingObjectStore.get("lang");

        if (!multilingual) {
            // 언어 데이터가 없다면 불러오기
            const requests = axios.create({ baseURL: window.location.origin });
            const res = await requests.get("/static/multilingual.yaml");
            multilingual = yaml.load(res.data) as ContentsObject;
            await generalObjectStore.put("multilingual", multilingual);
        }
        if (!lang) {
            // 언어 지정이 안되어있다면 기본값을 지정
            lang = multilingual["base"];
            await settingObjectStore.put("lang", lang);
        }

        // multilingual 객체에서 사용되는 모든 언어를 LangMap 객체로 파싱
        const langs: LangMap = {};
        const supportedLangs = new Set<string>();
        for (const text in multilingual) {
            const content = multilingual[text];
            if (text !== "base" && typeof content === "object") {
                for (const lang in content) {
                    supportedLangs.add(lang);
                }
                if (!content[multilingual.base]) {
                    throw new Error(
                        `${text} 항목에 대한 기본 언어(${multilingual.base})가 작성되지 않았습니다!`
                    );
                }
            }
        }
        supportedLangs.forEach((lang) => {
            langs[lang] = ISO6391.getName(lang);
        });

        // contents는 multilingual객체에서 base 속성을 제거한것이다.
        const contents = { ...multilingual };
        delete contents.base;

        return { pin: lang, langs, contents };
    }

    // 비동기라서 먼저 초기값을 세팅해야지 undifined 에러가 안남
    let langInfo: LangInfo = { pin: "", langs: {}, contents: {} };
    onMount(async () => {
        await generalObjectStore.delete("multilingual"); // 기존꺼 지우고
        langInfo = await loadMultilingual(); // 다시 로딩
    }); // 데이터 세팅: 새로고침 시 서버의 데이터가 다시 반영되도록

    let langMenuOn = false;
    async function toggleLangMenu() {
        langMenuOn = !langMenuOn;
    }
    async function langChange(event: Event) {
        const lang = (event.target as HTMLSelectElement).value;
        settingObjectStore.put("lang", lang); // 선택된 언어로 바꾸고
        window.location.reload(); // 새로고침
    }
</script>

<footer>
    <div class="lang">
        <button on:click={toggleLangMenu}>
            <object
                title="language setting button"
                data="/static/svg/multilingual.svg"
                type="image/svg+xml"
            />
        </button>
        <select
            class="lang__menu"
            class:none={!langMenuOn}
            value={langInfo.pin}
            on:change={langChange}
        >
            {#each Object.entries(langInfo.langs) as [code, name]}
                <option value={code}>{name}</option>
            {/each}
        </select>
    </div>
</footer>

<style>
    .lang {
        display: flex;
        width: 17rem;
        height: 3rem;
        position: fixed;
        bottom: 2rem;
        left: 2rem;
    }
    .lang button {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 3rem;
        height: 3rem;
        border-radius: 0.5rem;
        border: solid thin white;
        background: none;
        opacity: 0.6;

        pointer-events: all; /* for object element  */
    }
    .lang button object {
        width: 2rem;
        height: 2rem;
        pointer-events: none;
    }
    .lang button:hover {
        cursor: pointer;
        background-color: rgba(255, 255, 255, 0.16);
    }
    .lang__menu {
        background: none;
        opacity: 0.6;
        border-radius: 0.5rem;
        border: solid thin white;
        color: white;
        margin: 0 0.5rem;
        padding: 0 1rem;
        width: 11rem;
    }
    .lang__menu:hover {
        cursor: pointer;
        background-color: rgba(255, 255, 255, 0.16);
    }
</style>
