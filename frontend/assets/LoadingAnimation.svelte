<script>
    let bgColor = `hsl(${Math.random() * 360}, 100%, 85%)`;
    let dots = Array(8)
        .fill(0)
        .map((_, index) => index);
</script>

<section>
    <div class="loader" style="--bg: {bgColor}">
        {#each dots as dot}
            <div class="dot" style="--index: {dot}" />
        {/each}
    </div>
</section>

<style>
    section {
        align-items: center;
        display: flex;
        justify-content: center;
        width: 10rem;
        height: 10rem;
        overflow-x: hidden;
        --scale: 0.5;
        --dot-size: 5;
        --speed: 1.5;
        --radius: 10;
        --center-size: 5;
        --rotation: -25;
        --ring-radius: 8;
        --ring-thickness: 0.75;
        --bg: hsl(10, 100%, 85%);
    }

    .loader {
        position: relative;
        height: calc(var(--dot-size) * var(--center-size) * 1px);
        width: calc(var(--dot-size) * var(--center-size) * 1px);
        animation: turn calc(var(--speed) * 20s) calc(var(--speed) * -2s) infinite linear;
        transform: scale(var(--scale));
    }

    .loader:before {
        content: "";
        position: absolute;
        top: 50%;
        left: 50%;
        background: var(--bg);
        height: 100%;
        width: 100%;
        transform: translate(-50%, -50%);
        border-radius: 100%;
        animation: pulse calc(var(--speed) * 1s) infinite alternate-reverse;
    }

    .dot {
        height: calc(var(--dot-size) * 1px);
        width: calc(var(--dot-size) * 1px);
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%) rotate(calc((360 / 8) * var(--index) * 1deg))
            translate(0, calc(var(--dot-size) * var(--radius) * 1px));
    }

    .dot:after,
    .dot:before {
        content: "";
        border-radius: 100%;
        box-sizing: border-box;
        position: absolute;
        background: none;
        top: 50%;
        left: 50%;
        animation-duration: calc(var(--speed) * 1s);
        animation-delay: calc((8 - var(--index)) * (var(--speed) / 8) * -1s);
        animation-iteration-count: infinite;
        animation-timing-function: ease-in-out;
        animation-fill-mode: both;
        transform: translate(-50%, -50%) scale(var(--scale));
    }

    .dot:after {
        --dot-size: 5;
        --ring-thickness: 0.75;
        --ring-radius: 8;
        --scale: 0;
        animation-name: load;
        border: calc(var(--dot-size) * var(--ring-thickness) * 1px) solid var(--bg);
        height: calc(var(--dot-size) * var(--ring-radius) * 1px);
        width: calc(var(--dot-size) * var(--ring-radius) * 1px);
    }

    .dot:before {
        --scale: 1;
        animation-name: fade;
        background: var(--bg);
        height: 100%;
        width: 100%;
    }

    @keyframes fade {
        0% {
            opacity: 1;
        }
        85%,
        100% {
            opacity: 0.2;
        }
    }

    @keyframes load {
        0% {
            transform: translate(-50%, -50%) scale(0);
        }
        85%,
        100% {
            transform: translate(-50%, -50%) scale(1);
            opacity: 0;
        }
    }

    @keyframes pulse {
        to {
            opacity: 0.35;
        }
    }

    @keyframes turn {
        to {
            transform: rotate(-360deg) scale(var(--scale));
        }
    }
</style>
