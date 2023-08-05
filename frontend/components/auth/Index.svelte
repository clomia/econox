<script lang="ts">
    import * as state from "../../modules/state";
    import Login from "./Login.svelte";
    import Signup from "./signup/Index.svelte";
    import LoginSignupToggle from "./LoginSignupToggle.svelte";

    const toggleState = state.auth.toggle;
</script>

<!-- 
    로그인/회원가입 둘 중 뭘 하는지 여부를 나타내는 컴포넌트는 여기에 쓰고 
    단계별로 필요한 컴포넌트는 순수함수 파이프라인 아키텍쳐로 쓰게
    인자 받을 수 있는 별도의 컴포넌로 만들어서 쓰자
-->
<div id="fixed-ground">
    <div class="window">
        <LoginSignupToggle />
        <section>
            {#if $toggleState.login}
                <Login />
            {:else}
                <Signup />
            {/if}
        </section>
    </div>
</div>

<style>
    #fixed-ground {
        display: flex;
        justify-content: center;
        align-items: start;
        position: fixed;
        top: 10rem;
        left: 0;
        right: 0;
        bottom: 0;
    }
    .window {
        width: 34rem;
        padding: 3rem 4rem;
        border-radius: 1rem;
        border: thin solid rgba(255, 255, 255, 0.2);
        background: linear-gradient(to bottom, #2e2f32, rgb(32, 49, 55));
    }
</style>
