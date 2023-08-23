<script lang="ts">
    import * as state from "../../../modules/state";
    import LoadingAnimation from "../../../assets/LoadingAnimation.svelte";
    import LoadingTextAnimation from "../../../assets/LoadingTextAnimation.svelte";

    const inputResult = state.auth.signup.inputResult;
    const text = state.uiText.text;

    // 1. 일단 바로 로딩 화면부터 보여준 뒤
    // 2. inputResult 취합해서 POST /user (회원가입) 요청
    // 3. 성공 시:
    //     완료 문구와 확인 버튼을 띄운다.
    //     확인 버튼을 누르면 로그인 처리 해준다 (이메일,비번으로 /auth/user 요청을 통해 토큰 받아서 저장)
    //   실패 시:
    //      실패 문구와 실패 이유를 간단하게 보여주고 잠시 후 다시 시도해달라고 한다.
    //      확인 버튼 누르면 그냥 전부 취소됌
</script>

<main>
    <section class="loading">
        <LoadingTextAnimation />
        <div>
            <LoadingAnimation scale={2} />
        </div>
    </section>
    <!-- <div>{$text.sucessSignup}</div> -->
</main>

<style>
    main {
        display: flex;
        flex-direction: column;
        align-items: center;
        height: 17rem;
    }
    .loading {
        margin-top: 2rem;
    }
    .loading div {
        display: flex;
        justify-content: center;
        align-items: center;
    }
</style>
