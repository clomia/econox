<script>
    export let scale = 1;
</script>

<main>
    <div class="loading-container">
        <div class="loading-text" style="font-size: {scale * 2.8}rem;">
            <span>L</span>
            <span>O</span>
            <span>A</span>
            <span>D</span>
            <span>I</span>
            <span>N</span>
            <span>G</span>
        </div>
    </div>
</main>

<style>
    main {
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .loading-container {
        text-align: center;
        position: relative;
        color: rgba(255, 255, 255, 0.6);
    }
    .loading-container:before {
        content: "";
        position: absolute;
        width: 100%;
        height: 3px;
        background-color: rgba(255, 255, 255, 0.6);
        bottom: 1.7rem;
        left: 0;
        border-radius: 10px;
        animation: movingLine 2.4s infinite ease-in-out;
    }
    @keyframes movingLine {
        0% {
            opacity: 0;
            width: 0;
        }
        33.3%,
        66% {
            opacity: 0.8;
            width: 100%;
        }
        85% {
            width: 0;
            left: initial;
            right: 0;
            opacity: 1;
        }
        100% {
            opacity: 0;
            width: 0;
        }
    }
    .loading-text {
        font-size: 2.8rem;
        line-height: 64px;
        letter-spacing: 10px;
        margin-bottom: 1.5rem;
        display: flex;
        justify-content: space-evenly;
    }
    .loading-text span {
        animation: moveLetters 2.4s infinite ease-in-out;
        transform: translatex(0);
        position: relative;
        display: inline-block;
        opacity: 0;
        text-shadow: 0px 2px 10px rgba(46, 74, 81, 0.3);
    }
    .loading-text span:nth-child(1) {
        animation-delay: 0.1s;
    }
    .loading-text span:nth-child(2) {
        animation-delay: 0.2s;
    }
    .loading-text span:nth-child(3) {
        animation-delay: 0.3s;
    }
    .loading-text span:nth-child(4) {
        animation-delay: 0.4s;
    }
    .loading-text span:nth-child(5) {
        animation-delay: 0.5s;
    }
    .loading-text span:nth-child(6) {
        animation-delay: 0.6s;
    }
    .loading-text span:nth-child(7) {
        animation-delay: 0.7s;
    }
    @keyframes moveLetters {
        0% {
            transform: translateX(-15vw);
            opacity: 0;
        }
        33.3%,
        66% {
            transform: translateX(0);
            opacity: 1;
        }
        100% {
            transform: translateX(15vw);
            opacity: 0;
        }
    }
</style>
