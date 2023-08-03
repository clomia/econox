<script>
    import LoginSignupToggle from "./LoginSignupToggle.svelte";
    import Login from "./Login.svelte";
    import Signup from "./signup/Index.svelte";
    $: toggle = { login: true, signup: false };
</script>

<!-- 
    로그인/회원가입 둘 중 뭘 하는지 여부를 나타내는 컴포넌트는 여기에 쓰고 
    단계별로 필요한 컴포넌트는 순수함수 파이프라인 아키텍쳐로 쓰게
    인자 받을 수 있는 별도의 컴포넌로 만들어서 쓰자
-->
<div id="fixed-ground">
    <div class="window">
        <LoginSignupToggle bind:toggle />
        <section>
            {#if toggle.login}
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
        border: solid thin white;
        background: #606c88;
        /* fallback for old browsers */
        background: -webkit-linear-gradient(to bottom, #5e6c8e, #51798a, #5e6c8e);
        /* Chrome 10-25, Safari 5.1-6 */
        background: linear-gradient(to bottom, #5e6c8e, #51798a, #5e6c8e);
        /* W3C, IE 10+/ Edge, Firefox 16+, Chrome 26+, Opera 12+, Safari 7+ */

        background: #834d9b;
        background: -webkit-linear-gradient(to top, #d04ed6, #834d9b);
        background: linear-gradient(to top, #d04ed6, #834d9b);
    }
</style>
