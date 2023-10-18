<script>
    let n = 6;
</script>

<main>
    <div class="a" style="--n: {n}">
        {#each Array(n).fill() as _, i}
            <div class="dot" style="--i: {i}" />
        {/each}
    </div>
</main>

<style>
    :root {
        --d: 1rem; /* 크기를 2배 작게 만듭니다 */
        --t: 1s;
    }

    main {
        color: rgb(31, 36, 39);
        text-align: center;
    }

    .a {
        width: 100%;
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        align-items: center;
    }

    .dot {
        background: rgba(255, 255, 255, 0.4);
        box-shadow: 0 0 0.5rem 0.1rem rgba(255, 255, 255, 0.1);
        margin: 0 0.25rem;
    }

    .dot,
    .dot:after {
        display: inline-block;
        width: var(--d);
        height: var(--d);
        border-radius: 50%;
        animation: a var(--t) calc(((var(--i) + var(--o, 0)) / var(--n) - 1) * var(--t)) infinite;
    }

    .dot:after {
        --o: 1;
        background: currentcolor;
        content: "";
    }

    @keyframes a {
        0%,
        50% {
            transform: scale(0);
        }
    }
</style>
