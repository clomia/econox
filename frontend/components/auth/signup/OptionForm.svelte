<script>
</script>

<main>
    <div class="title">맴버십 선택</div>
    <div class="subtitle">
        첫 회원가입 고객을 대상으로 선택한 맴버십이 첫 한달간 결제 없이 무료로 제공됩니다!
    </div>

    <div class="forex-toggle">
        <div class="forex-toggle__mover" />
        <button>달러 요금제</button>
        <button>원화 요금제</button>
    </div>

    <div class="additional">달러 요금제는 한국 결제수단을 지원하지 않습니다.</div>

    <button class="basic">
        <div class="basic__title">일반</div>
        <div class="basic__price">15,000원</div>
        <p>
            전세계 금융시장, 국가경제, 기업 데이터를 비교해서 연관성을 발견하세요. 모든 데이터를 시계열
            그래프로 비교해서 거시경제를 한눈에 파악하고 투자에 필요한 통찰을 얻을 수 있습니다.
        </p>
    </button>

    <button class="professional">
        <div class="professional__title">전문가</div>
        <div class="professional__price">19,000원</div>
        <p>모든 데이터를 CSV로 무제한 다운로드할 수 있습니다!</p>
    </button>
</main>

<style>
    main {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 0 1rem;
    }
    .title {
        color: aqua;
        font-size: 1.2rem;
        padding-top: 2.1rem;
        padding-bottom: 1.3rem;
    }
    .subtitle {
        color: rgba(255, 255, 255, 0.8);
        text-align: center;
        padding: 0 1rem;
    }

    .forex-toggle {
        display: flex;
        justify-content: space-around;
        align-items: center;
        height: 3rem;
        width: 100%;
        margin-top: 2rem;
        border: thin solid white;
        border-radius: 2rem;
        position: relative;
    }
    .forex-toggle__mover {
        position: absolute;
        left: 0;
        width: 50%;
        height: inherit;
        border: inherit;
        border-radius: inherit;
        border-color: aqua;
        transition: left 200ms;
    }
    .forex-toggle button {
        color: white;
    }
    .forex-toggle:hover .forex-toggle__mover {
        left: 50%;
    }

    .additional {
        height: 1.2rem;
        margin: 1.2rem 0;
        font-size: 0.9rem;
        color: rgba(255, 255, 255, 0.7);
    }

    .basic,
    .professional {
        color: white;
        border: thin solid white;
        border-radius: 1rem;
        padding: 1.2rem;
    }
    .basic {
        margin-bottom: 2rem;
    }
    .basic__title,
    .professional__title {
        padding-bottom: 0.7rem;
        color: aqua;
    }
    .basic__price,
    .professional__price {
        padding-bottom: 0.5rem;
        color: rgba(255, 255, 255, 0.7);
    }
    p {
        color: rgba(255, 255, 255, 0.8);
    }

    button:hover,
    .forex-toggle:hover {
        cursor: pointer;
    }
</style>
