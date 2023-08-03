<script lang="ts">
    import axios from "axios";
    import type { AxiosResponse } from "axios";
    import LoadingAnimation from "../../../assets/LoadingAnimation.svelte";
    export let text: { [key: string]: string };

    let request: string | Promise<AxiosResponse> = "before"; // 요청 전
    async function signup(event: SubmitEvent) {
        const requests = axios.create({ baseURL: window.location.origin });
        const form = event.target as HTMLFormElement;
        const email = form.email.value;
        const password = form.password.value;
        const retypePassword = form.retypePassword.value;
        // 둘이 똑같은지 검증은 여기서 하는게 여러모로 가장 견고한 로직임
        request = requests.post("/api/auth/user", { email, password });
        try {
            const token = (await request).data;
            // 여기서는 성공 동작만 처리하면 됌
            token["idToken"];
            token["refreshToken"];
            console.log("로그인 성공! -> 토큰 저장하고 콘솔로 보내주기!");
        } catch (error) {
            if (error.response.status === 401) {
                request = "fail"; // 로그인 실패
            } else {
                request = "error"; // 에러
            }
        }
    }
</script>

<form on:submit|preventDefault={signup}>
    <section>
        <label>
            <span>{text.email}</span>
            <input type="text" name="email" required />
        </label>
    </section>
    <section>
        <label>
            <span>{text.password}</span>
            <input type="password" name="password" required />
        </label>
    </section>
    <section>
        <label>
            <span>{text.retypePassword}</span>
            <input type="password" name="retypePassword" required />
        </label>
    </section>
    {#await request}
        <LoadingAnimation />
    {/await}
    {#if request == "fail"}
        <div>{text.signupFailed}</div>
    {:else if request == "error"}
        <div>{text.error}</div>
    {/if}
    {#if !(request instanceof Promise)}
        <button type="submit">{text.signup}</button>
    {/if}
</form>

<style>
    form {
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 100%;
        height: 21rem;
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
