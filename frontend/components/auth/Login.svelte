<script lang="ts">
    import LoadingAnimation from "../../assets/LoadingAnimation.svelte";
    import * as state from "../../modules/state";
    import { publicRequest } from "../../modules/api";

    import type { AxiosResponse } from "axios";

    const text = state.uiText.text;

    let message = "";
    let request: string | Promise<AxiosResponse> = "before"; // 요청 전
    const login = async (event: SubmitEvent) => {
        const form = event.target as HTMLFormElement; //타입스크립트 적용 ㄱ
        const email = form.email.value;
        const password = form.password.value;
        if (!email || !password) {
            message = $text.missingInput;
            return;
        }
        try {
            request = publicRequest.post("/auth/user", { email, password });
            const token = (await request).data;
            // 여기서는 성공 동작만 처리하면 됌
            console.log(token["id_token"]);
            console.log(token["refresh_token"]);
            console.log("로그인 성공! -> 토큰 저장하고 콘솔로 보내주기!");
        } catch (error) {
            message = error.response?.status === 401 ? $text.loginFailed : $text.error;
        }
    };
</script>

<form on:submit|preventDefault={login}>
    <section>
        <label>
            <span>{$text.email}</span>
            <input type="text" name="email" autocomplete="email" />
        </label>
    </section>
    <section>
        <label>
            <span>{$text.password}</span>
            <input type="password" name="password" autocomplete="current-password" />
        </label>
    </section>
    {#await request}
        <LoadingAnimation />
    {/await}
    <div>{message}</div>
    {#if !(request instanceof Promise)}
        <button type="submit">{$text.login}</button>
    {/if}
</form>

<style>
    form {
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 100%;
        height: 16rem;
        margin-top: 2.5rem;
        color: white;
    }
    section {
        width: 24.5rem;
        margin-bottom: 1.7rem;
    }
    label span {
        display: block;
        color: rgba(255, 255, 255, 0.5);
        padding-left: 0.7rem;
        padding-bottom: 0.2rem;
        transition: color 100ms ease-out;
    }
    input {
        width: 100%;
        height: 2.5rem;
        border: solid thin white;
        border-radius: 0.7rem;
        color: white;
        padding-left: 1rem;
    }
    section:focus-within label span {
        color: rgba(255, 255, 255, 1);
    }
    button {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 15rem;
        height: 2.5rem;
        border: solid thin white;
        border-radius: 1rem;
        color: white;
        margin-top: 1.4rem;
    }
    button:hover {
        cursor: pointer;
        background-color: rgba(255, 255, 255, 0.2);
    }
</style>
