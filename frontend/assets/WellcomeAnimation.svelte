<main>
    <div class="animation01">
        <div class="rhombus_small">
            <div class="rhombus">
                <div class="border_box">
                    <span class="line line01" />
                    <span class="line line02" />
                    <span class="line line03" />
                    <span class="line line04" />
                    <span class="circle circle01" />
                    <span class="circle circle02" />
                    <span class="circle circle03" />
                    <span class="circle circle04" />
                    <span class="animation_line animation_line01" />
                    <span class="animation_line_wrapper animation_line02_wrapper"
                        ><span class="animation_line animation_line02" /></span
                    >
                    <span class="animation_line animation_line03" />
                    <span class="animation_line_wrapper animation_line04_wrapper"
                        ><span class="animation_line animation_line04" /></span
                    >
                    <span class="animation_line animation_line05" />
                    <span class="animation_line_wrapper animation_line06_wrapper"
                        ><span class="animation_line animation_line06" /></span
                    >
                    <span class="animation_line animation_line07" />
                    <span class="animation_line_wrapper animation_line08_wrapper"
                        ><span class="animation_line animation_line08" /></span
                    >
                </div>
                <div class="wave">
                    <div class="wave_wrapper"><div class="wave_box" /></div>
                </div>
            </div>
        </div>
    </div>
    <div class="animation02">
        <div class="rhombus_box">
            <span class="rhombus_item_wrapper rhombus_item01_wrapper"><span class="rhombus_item" /></span>
            <span class="rhombus_item_wrapper rhombus_item02_wrapper"><span class="rhombus_item" /></span>
        </div>
        <div class="double_content">
            <div class="double_wrapper02 dotted02">
                <div class="dotted_hide">
                    <div class="double_wrapper01 dotted01"><span class="dotted_right" /></div>
                </div>
            </div>
            <div class="double_wrapper02 white02"><div class="double_wrapper01 white01" /></div>
            <div class="double_wrapper02 gray02"><div class="double_wrapper01 gray01" /></div>
            <div class="double_wrapper02 orange02"><div class="double_wrapper01 orange01" /></div>
        </div>
        <div class="name">
            <span class="clomia">clomia</span>
            <p>WELLCOME</p>
            <span class="econox">ECONOX</span>
            <span class="name_circle01" />
            <span class="name_circle02" />
        </div>
    </div>
</main>

<style>
    /*================= Basic style ==================*/
    main {
        position: relative;
        width: 100%;
        height: 100%;
        overflow: hidden;
    }
    .econox {
        position: absolute;
        width: 100%;
        text-align: center;
        bottom: 4rem;
        opacity: 0.3;
    }
    .clomia {
        position: absolute;
        width: 100%;
        text-align: center;
        top: 4rem;
        font-family: "Allura", cursive;
        font-size: 1.5rem;
        color: aqua;
    }
    /*=================== animation01 ====================*/
    .animation01 {
        position: absolute;
        width: 100%;
        height: 100%;
    }
    .border_box {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 7.5rem;
        height: 7.5rem;
    }
    .line {
        display: block;
        position: absolute;
        right: 0;
        bottom: 0;
        background-color: #845b46;
        opacity: 0;
    }
    .line01 {
        top: 0;
        left: 100%;
        width: 0.075rem;
        height: 7.575rem;
        transform-origin: bottom;
        animation: animation01_line01 0.2s linear 0.3s forwards;
    }
    .line03 {
        top: 0;
        left: 0;
        width: 0.075rem;
        height: 7.575rem;
        transform-origin: bottom;
        animation: animation01_line01 0.2s linear 0.6s forwards;
    }
    @keyframes animation01_line01 {
        0% {
            transform: scale3d(1, 0, 1);
            opacity: 1;
        }
        100% {
            transform: scale3d(1, 1, 1);
            opacity: 1;
        }
    }
    .line02 {
        top: 100%;
        left: 0;
        width: 7.575rem;
        height: 0.075rem;
        transform-origin: right;
        animation: animation01_line02 0.2s linear 0.4s forwards;
    }
    .line04 {
        top: 0;
        left: 0;
        width: 7.575rem;
        height: 0.075rem;
        transform-origin: left;
        animation: animation01_line02 0.2s linear 0.8s forwards;
    }
    @keyframes animation01_line02 {
        0% {
            transform: scale3d(0, 1, 1);
            opacity: 1;
        }
        100% {
            transform: scale3d(1, 1, 1);
            opacity: 1;
        }
    }
    .circle {
        display: block;
        position: absolute;
        right: 0;
        bottom: 0;
        width: 0.6rem;
        height: 0.6rem;
        border: 0.05rem solid #fff;
        border-radius: 50%;
        opacity: 0;
    }
    .circle01 {
        top: 96%;
        left: 96%;
        margin: 0 auto;
        animation: animation01_circle 0.3s linear 0.3s forwards;
    }
    .circle02 {
        top: 96%;
        left: -99%;
        margin: 0 auto;
        animation: animation01_circle 0.3s linear 0.45s forwards;
    }
    .circle03 {
        top: -4%;
        left: -99%;
        margin: 0 auto;
        animation: animation01_circle 0.3s linear 0.65s forwards;
    }
    .circle04 {
        top: -4%;
        left: 96%;
        margin: 0 auto;
        animation: animation01_circle 0.3s linear 0.85s forwards;
    }
    @keyframes animation01_circle {
        0% {
            transform: scale3d(0, 0, 1);
            opacity: 1;
        }
        40% {
            transform: scale3d(1, 1, 1);
            opacity: 1;
        }
        60% {
            transform: scale3d(1, 1, 1);
            opacity: 1;
        }
        100% {
            transform: scale3d(0, 0, 1);
            opacity: 1;
        }
    }

    .wave {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 6.75rem;
        height: 6.75rem;
        overflow: hidden;
    }
    .wave_wrapper {
        width: 200%;
        height: 150%;
        position: absolute;
        top: -25%;
        right: 0;
        bottom: 0;
        left: -50%;
        margin: 0 auto;
        animation: animation01_wave_wrapper 1s linear 1s forwards;
    }
    @keyframes animation01_wave_wrapper {
        0% {
            transform: rotate(0);
        }
        25% {
            transform: rotate(15deg);
        }
        50% {
            transform: rotate(0);
        }
        75% {
            transform: rotate(-15deg);
        }
        100% {
            transform: rotate(0);
        }
    }
    .wave_box {
        position: absolute;
        top: 0;
        right: 0;
        bottom: 0;
        left: 0;
        margin: 0 auto;
        width: 100%;
        height: 100%;
        background-color: #fff;
        transform-origin: bottom;
        animation: animation01_wave_box 1s linear 1s forwards;
        opacity: 0;
    }
    @keyframes animation01_wave_box {
        0% {
            transform: scale3d(1, 0, 1);
            opacity: 1;
        }
        100% {
            transform: scale3d(1, 1, 1);
            opacity: 1;
        }
    }
    .animation_line {
        position: absolute;
        right: 0;
        bottom: 0;
        margin: 0 auto;
        background-color: #fff;
        opacity: 0;
    }
    .animation_line_wrapper {
        position: absolute;
        top: 0;
        right: 0;
        bottom: 0;
        left: 0;
        margin: 0 auto;
        width: 100%;
        height: 100%;
    }
    .animation_line01 {
        top: -15%;
        left: 0;
        width: 0.1rem;
        height: 0.35rem;
        animation: animation_line01 0.3s cubic-bezier(0.165, 0.84, 0.44, 1) 1.9s;
        transform-origin: top;
    }
    .animation_line02_wrapper {
        transform: rotate(45deg);
    }
    .animation_line02 {
        top: -35%;
        left: 0;
        width: 0.1rem;
        height: 0.35rem;
        animation: animation_line01 0.3s cubic-bezier(0.165, 0.84, 0.44, 1) 1.9s;
        transform-origin: top;
    }
    @keyframes animation_line01 {
        0% {
            transform: translateY(0);
            opacity: 1;
        }
        100% {
            transform: translateY(-0.75rem);
            opacity: 1;
        }
    }
    .animation_line03 {
        top: 50%;
        left: 110%;
        width: 0.35rem;
        height: 0.1rem;
        animation: animation_line03 0.3s cubic-bezier(0.165, 0.84, 0.44, 1) 1.9s;
        transform-origin: right;
    }
    .animation_line04_wrapper {
        transform: rotate(45deg);
    }
    .animation_line04 {
        top: 50%;
        left: 128%;
        width: 0.35rem;
        height: 0.1rem;
        animation: animation_line03 0.3s cubic-bezier(0.165, 0.84, 0.44, 1) 1.9s;
        transform-origin: right;
    }
    @keyframes animation_line03 {
        0% {
            transform: translateX(0);
            opacity: 1;
        }
        100% {
            transform: translateX(0.75rem);
            opacity: 1;
        }
    }
    .animation_line05 {
        top: 110%;
        left: 0;
        width: 0.1rem;
        height: 0.35rem;
        animation: animation_line05 0.3s cubic-bezier(0.165, 0.84, 0.44, 1) 1.9s;
        transform-origin: bottom;
    }
    .animation_line06_wrapper {
        transform: rotate(45deg);
    }
    .animation_line06 {
        top: 128%;
        left: 0;
        width: 0.1rem;
        height: 0.35rem;
        animation: animation_line05 0.3s cubic-bezier(0.165, 0.84, 0.44, 1) 1.9s;
        transform-origin: bottom;
    }
    @keyframes animation_line05 {
        0% {
            transform: translateY(0);
            opacity: 1;
        }
        100% {
            transform: translateY(0.75rem);
            opacity: 1;
        }
    }
    .animation_line07 {
        top: 50%;
        left: -130%;
        width: 0.35rem;
        height: 0.1rem;
        animation: animation_line07 0.3s cubic-bezier(0.165, 0.84, 0.44, 1) 1.9s;
        transform-origin: left;
    }
    .animation_line08_wrapper {
        transform: rotate(45deg);
    }
    .animation_line08 {
        top: 50%;
        left: -162%;
        width: 0.35rem;
        height: 0.1rem;
        animation: animation_line07 0.3s cubic-bezier(0.165, 0.84, 0.44, 1) 1.9s;
        transform-origin: left;
    }
    @keyframes animation_line07 {
        0% {
            transform: translateX(0);
            opacity: 1;
        }
        100% {
            transform: translateX(-0.75rem);
            opacity: 1;
        }
    }

    .rhombus {
        position: absolute;
        width: 100%;
        height: 100%;
        animation: rhombus 0.2s linear 2.2s forwards;
    }
    @keyframes rhombus {
        0% {
            transform: rotate(0);
        }
        100% {
            transform: rotate(45deg);
        }
    }
    .rhombus_small {
        position: absolute;
        width: 100%;
        height: 100%;
        animation: rhombus_small 0.4s linear 2.55s forwards;
    }
    @keyframes rhombus_small {
        0% {
            transform: scale3d(1, 1, 1);
            opacity: 1;
        }
        99% {
            transform: scale3d(0.15, 0.15, 0.15);
            opacity: 1;
        }
        100% {
            transform: scale3d(0.15, 0.15, 0.15);
            opacity: 0;
        }
    }

    /*=================== animation02 ====================*/
    .animation02 {
        position: absolute;
        width: 100%;
        height: 100%;
    }
    .rhombus_box {
        position: absolute;
        top: 0;
        right: 0;
        bottom: 0;
        left: 0;
        margin: auto;
        width: 20rem;
        height: 20rem;
        animation: rhombus_box 0.4s linear 3.55s forwards;
    }
    .rhombus_item_wrapper {
        position: absolute;
        top: 0;
        right: 0;
        bottom: 0;
        left: 0;
        margin: auto;
        width: 1.05rem;
        height: 1.05rem;
        opacity: 0;
    }
    .rhombus_item {
        position: absolute;
        top: 0;
        right: 0;
        bottom: 0;
        left: 0;
        margin: auto;
        width: 1.05rem;
        height: 1.05rem;
        background-color: #fff;
        transform: rotate(45deg);
    }
    .rhombus_item01_wrapper {
        animation: rhombus_item01 0.5s linear 2.95s forwards;
    }

    .rhombus_item02_wrapper {
        animation: rhombus_item02 0.5s linear 2.95s forwards;
    }
    @keyframes rhombus_item01 {
        0% {
            transform: translateX(0);
            opacity: 1;
        }
        100% {
            transform: translateX(-9.25rem);
            opacity: 1;
        }
    }
    @keyframes rhombus_item02 {
        0% {
            transform: translateX(0);
            opacity: 1;
        }
        100% {
            transform: translateX(9.25rem);
            opacity: 1;
        }
    }
    @keyframes rhombus_box {
        0% {
            transform: rotate(0);
        }
        100% {
            transform: rotate(360deg);
        }
    }

    .double_content {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 100%;
        height: 100%;
    }
    .double_wrapper02 {
        position: relative;
        width: 100%;
        height: 100%;
        animation: double_content forwards;
        opacity: 0;
    }
    .double_wrapper01 {
        display: block;
        position: absolute;
        border-radius: 50%;
        overflow: hidden;
    }
    .double_wrapper01::before {
        content: "";
        display: block;
        position: absolute;
        background: #212022;
        z-index: 2;
    }
    .double_wrapper01::after {
        content: "";
        display: block;
        position: absolute;
        background: #212022;
        z-index: 3;
    }
    /*============
dotted circle
============*/
    .dotted02 {
        top: 0;
        animation-delay: 4.2s;
    }
    .dotted_hide {
        position: absolute;
        width: 15.5rem;
        height: 15.5rem;
        z-index: 1;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        border-radius: 50%;
        overflow: hidden;
    }
    .dotted01 {
        width: 15rem;
        height: 15rem;
        border: dotted 0.25rem #fff;
        z-index: 1;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        overflow: visible;
    }
    .dotted_right::before {
        content: "";
        display: block;
        position: absolute;
        background: #212022;
        z-index: 3;
    }
    .dotted_right::before {
        top: 0;
        left: 0;
        width: 16rem;
        height: 16rem;
        transform-origin: left 8rem;
        animation: rotate-circle-right 0.5s linear 4.2s forwards;
    }
    .dotted_right {
        position: absolute;
        width: 8rem;
        height: 16rem;
        z-index: 1;
        top: 50%;
        left: 75%;
        transform: translate(-50%, -50%);
        overflow: hidden;
    }
    .dotted01::after {
        top: -0.5rem;
        left: -8.5rem;
        width: 16rem;
        height: 16rem;
        transform-origin: right 8rem;
        animation: rotate-circle-left01 0.5s linear 4.2s forwards;
    }
    @keyframes rotate-circle-left01 {
        0% {
            transform: rotate(0deg);
            background: #212022;
            opacity: 1;
        }
        50% {
            transform: rotate(-180deg);
            background: #212022;
            opacity: 1;
        }
        50.01% {
            transform: rotate(0deg);
            opacity: 0;
        }
        100% {
            transform: rotate(0deg);
            opacity: 0;
        }
    }
    /*============ white circle ============*/
    .white02 {
        top: -100%;
        animation-delay: 4.7s;
    }
    .white01 {
        width: 14.5rem;
        height: 14.5rem;
        background: #fff;
        z-index: 1;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
    }
    .white01::before {
        top: 0;
        left: 7.25rem;
        width: 14.5rem;
        height: 14.5rem;
        transform-origin: left 7.25rem;
        animation: rotate-circle-right 0.3s linear 4.7s forwards;
    }
    .white01::after {
        top: 0;
        left: -7.25rem;
        width: 14.5rem;
        height: 14.5rem;
        transform-origin: right 7.25rem;
        animation: rotate-circle-left 0.3s linear 4.7s forwards;
    }
    @keyframes rotate-circle-left {
        0% {
            transform: rotate(0deg);
            background: #212022;
        }
        50% {
            transform: rotate(-180deg);
            background: #212022;
        }
        50.01% {
            transform: rotate(-360deg);
            background: #fff;
        }
        100% {
            transform: rotate(-360deg);
            background: #fff;
        }
    }
    /*============ gray circle ============*/
    .gray02 {
        top: -200%;
        animation-delay: 4.8s;
    }
    .gray01 {
        width: 4rem;
        height: 4rem;
        background: #808184;
        z-index: 1;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
    }
    .gray01::before {
        top: 0;
        left: 2rem;
        width: 4rem;
        height: 4rem;
        background: #fff;
        transform-origin: left 2rem;
        animation: rotate-circle-right 0.5s linear 4.8s forwards;
    }
    .gray01::after {
        top: 0;
        left: -2rem;
        width: 4rem;
        height: 4rem;
        background: #fff;
        transform-origin: right 2rem;
        animation: rotate-circle-left03 0.5s linear 4.8s forwards;
    }
    @keyframes rotate-circle-left03 {
        0% {
            transform: rotate(0deg);
            background: #fff;
        }
        50% {
            transform: rotate(-180deg);
            background: #fff;
        }
        50.01% {
            transform: rotate(-360deg);
            background: #808184;
        }
        100% {
            transform: rotate(-360deg);
            background: #808184;
        }
    }
    /*============ orange circle ============*/
    .orange02 {
        top: -300%;
        animation-delay: 5.3s;
    }
    .orange01 {
        width: 13.5rem;
        height: 13.5rem;
        background: #1f3036;
        z-index: 1;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
    }
    .orange01::before {
        top: 0;
        left: 6.75rem;
        width: 13.5rem;
        height: 13.5rem;
        background: #fff;
        transform-origin: left 6.75rem;
        animation: rotate-circle-right 0.5s linear 5.3s forwards;
    }
    .orange01::after {
        top: 0;
        left: -6.75rem;
        width: 13.5rem;
        height: 13.5rem;
        background: #fff;
        transform-origin: right 6.75rem;
        animation: rotate-circle-left02 0.5s linear 5.3s forwards;
    }
    @keyframes rotate-circle-left02 {
        0% {
            transform: rotate(0deg);
            background: #fff;
        }
        50% {
            transform: rotate(-180deg);
            background: #fff;
        }
        50.01% {
            transform: rotate(-360deg);
            background: #1f3036;
        }
        100% {
            transform: rotate(-360deg);
            background: #1f3036;
        }
    }

    @keyframes double_content {
        0% {
            opacity: 0;
        }
        100% {
            opacity: 1;
        }
    }
    @keyframes rotate-circle-right {
        0% {
            transform: rotate(0deg);
        }
        50% {
            transform: rotate(0deg);
        }
        100% {
            transform: rotate(-180deg);
        }
    }

    .name {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 15rem;
        height: 15rem;
        animation: name 1s cubic-bezier(0.165, 0.84, 0.44, 1) 5.9s forwards;
        opacity: 0;
    }
    .name p {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        color: #fff;
        font-size: 1.2rem;
        letter-spacing: 0.1em;
    }
    .name_circle01 {
        position: absolute;
        top: 50%;
        left: 15%;
        transform: translate(-50%, -50%);
        background-color: #fff;
        width: 1rem;
        height: 1rem;
        border-radius: 50%;
    }
    .name_circle02 {
        position: absolute;
        top: 50%;
        left: 85%;
        transform: translate(-50%, -50%);
        background-color: #fff;
        width: 1rem;
        height: 1rem;
        border-radius: 50%;
    }
    @keyframes name {
        0% {
            opacity: 0;
        }
        100% {
            opacity: 1;
        }
    }
</style>
