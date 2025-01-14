<script lang="ts">
  import ColorPicker from "svelte-awesome-color-picker";
  import { api } from "../../../modules/request";
  import {
    Text,
    FeatureGroups,
    FeatureGroupSelected,
    CountryCodeMap,
  } from "../../../modules/state";
  import { featureAddDeleteHandler } from "./functions";
  import CircleLoader from "../../../assets/animation/CircleLoader.svelte";
  import EditIcon from "../../../assets/icon/EditIcon.svelte";
  import MinusIcon from "../../../assets/icon/MinusIcon.svelte";
  import DownloadIcon from "../../../assets/icon/DownloadIcon.svelte";
  import Download from "../univariate-tool/chart/Download.svelte";
  import type { FeatureType } from "../../../modules/state";

  interface color {
    r: number;
    g: number;
    b: number;
    a: number;
  }

  let main: HTMLElement;
  let colorHovered: FeatureType | null = null;
  let colorPickerOn: FeatureType | null = null;
  let colorPicked: color | null = null;
  let colorBeforeApply: color | null = null;
  let colorPickerPositionTop: number = 96;
  let colorPickerElement: HTMLElement | null = null;

  /**
   * 컬러 피커 밖을 클릭하면 해당 색상이 적용되도록 구현하기 위해서
   * 요소 밖이 클릭되는 이벤트를 감지합니다.
   */
  const clickOutside = (node: HTMLElement, onOutsideClick: () => void) => {
    const handleClick = (event: MouseEvent) => {
      if (!node.contains(event.target as Node) && !event.defaultPrevented) {
        onOutsideClick();
      }
    };
    document.addEventListener("click", handleClick, true);
    return {
      destroy() {
        document.removeEventListener("click", handleClick, true);
      },
    };
  };

  /**
   * rgb(r,g,b) 형식의 문자열을 ColorPicker 호환 RGBA 객체로 변환합니다.
   */
  const colorEncode = (colorString: string) => {
    const regex = /rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)/;
    const match = colorString.trim().match(regex);

    if (match) {
      // 구조 분해 할당을 사용하여 매치된 값을 변수에 바로 할당
      const [, r, g, b] = match.map(Number);
      // 객체 리터럴 단축 속성명을 사용하여 객체 생성 및 반환
      return { r, g, b, a: 1 };
    } else {
      throw new Error("Invalid input format");
    }
  };
  const colorDecode = ({ r, g, b }) => `rgb(${r}, ${g}, ${b})`;

  const colorUpdate = async () => {
    const request = {
      // 요청 본문 정의
      group_id: $FeatureGroupSelected.id,
      element: {
        section: colorPickerOn.element.section,
        code: colorPickerOn.element.code,
      },
      factor: {
        section: colorPickerOn.factor.section,
        code: colorPickerOn.factor.code,
      },
      target: {
        color: colorDecode(colorPicked),
      },
    };
    colorPickerOn = null;
    if (colorBeforeApply === colorPicked) {
      return; // 변경사항이 없으므로 API 요청 안보냄
    } else {
      colorBeforeApply = colorPicked;
      // 이제 적용될거니까 동일한 API 요청이 없도록 업데이트
    }
    await api.member.patch("/feature/group/feature", request);
  };

  const onColorPicker = (feature: FeatureType) => {
    const initColor = colorEncode(feature.color);
    const index = $FeatureGroupSelected.features.findIndex(
      (f) => f === feature
    ); // overflow를 처리하기 위해 해당 DOM 높이를 기반으로 위젯의 위치를 계산해야 함
    const liElement = main.getElementsByClassName("li")[index];
    colorPickerPositionTop = liElement.clientHeight + 9; // 9가 가장 적절함
    colorPickerOn = feature;
    colorPicked = initColor;
    colorBeforeApply = initColor;
  };

  $: if (colorPickerOn && colorPicked) {
    // 전역 스토어에 색상 변경 사항을 실시간으로 반영합니다.
    const target = colorPickerOn;
    const newColor = colorDecode(colorPicked);

    // 복사
    let updated = $FeatureGroupSelected;
    let updatedGroups = $FeatureGroups;

    const targetIndex = updatedGroups.findIndex(
      (group) => group === $FeatureGroupSelected
    );

    // 변경사항 반영
    updated.features.find((f) => f === target).color = newColor;
    updatedGroups[targetIndex] = updated;

    // 변경사항 적용
    $FeatureGroupSelected = updated;
    $FeatureGroups = updatedGroups;
  }

  const scrollToTargetElement = (
    container: HTMLElement,
    targetElement: HTMLElement
  ) => {
    const containerRect = container.getBoundingClientRect();
    const targetRect = targetElement.getBoundingClientRect();

    // 대상 요소의 하단이 컨테이너의 하단으로부터 얼마나 떨어져 있는지 계산
    const relativeBottom = targetRect.bottom - containerRect.top;

    // 컨테이너의 높이를 고려하여 실제 스크롤 위치 계산
    const scrollToPosition =
      relativeBottom - container.clientHeight + container.scrollTop;

    container.scrollTo({
      top: scrollToPosition,
      behavior: "smooth",
    });
  };

  $: if (colorPickerElement) {
    // 컬러 피커 요소가 나타나면 해당 요소가 잘 보이도록 스크롤 이동
    scrollToTargetElement(main, colorPickerElement);
  }

  let isLoading = false;
  const del = async (feature: FeatureType) => {
    isLoading = true;
    document.body.style.overflow = "hidden";

    // 복사
    let updated = { ...$FeatureGroupSelected };
    let updatedGroups = [...$FeatureGroups];

    const targetGroupId = updated.id;
    let targetIndex = updatedGroups.findIndex(
      (group) => group.id === targetGroupId
    );
    await api.member.delete("/feature/group/feature", {
      data: {
        group_id: targetGroupId,
        element: {
          section: feature.element.section,
          code: feature.element.code,
        },
        factor: {
          section: feature.factor.section,
          code: feature.factor.code,
        },
      },
    });
    // 변경사항 반영
    updated.features = updated.features.filter((f) => f !== feature);
    updatedGroups[targetIndex] = updated;
    // 변경사항 적용
    $FeatureGroupSelected = updated;
    $FeatureGroups = updatedGroups;
    isLoading = false;
    document.body.style.overflow = "";
    featureAddDeleteHandler(targetGroupId);
  };

  let featureListHeight = 3;
  $: {
    // 계산 시작
    let value = 0;
    if (!$FeatureGroupSelected.features.length) {
      value = 3;
    } else if ($FeatureGroupSelected.features.length <= 2) {
      value = 11;
    } else {
      value = $FeatureGroupSelected.features.length * 5.4;
    }
    // 계산 종료
    // 할당 (27가 최대치임, 딱 5개 들어감)
    if (value > 27 || colorPickerOn) {
      featureListHeight = 27;
    } else {
      featureListHeight = value;
    }
  }

  let downloadWidget: boolean = false;
  let downloadTarget = {
    elementSection: "",
    elementCode: "",
    factorSection: "",
    factorCode: "",
  };
  const download = (feature: FeatureType) => {
    downloadTarget.elementSection = feature.element.section;
    downloadTarget.elementCode = feature.element.code;
    downloadTarget.factorSection = feature.factor.section;
    downloadTarget.factorCode = feature.factor.code;
    downloadWidget = true;
  };
</script>

{#if isLoading}
  <div class="loader"><CircleLoader /></div>
{/if}

<main bind:this={main} style="height: {featureListHeight}rem;">
  {#each $FeatureGroupSelected.features as feature}
    <div class="li">
      <button
        class="li__colorbox"
        style="background-color: {feature.color};"
        class:border-none={colorHovered === feature}
        class:hover-none={colorPickerOn === feature}
        on:click={() => onColorPicker(feature)}
        on:mouseenter={() => (colorHovered = feature)}
        on:mouseleave={() => (colorHovered = null)}
      >
        {#if colorHovered === feature && colorPickerOn !== feature}
          <div class="li__colorbox__edit-icon"><EditIcon /></div>
        {/if}
      </button>
      {#if colorPickerOn === feature}
        <div
          class="li__colorpicker"
          use:clickOutside={colorUpdate}
          bind:this={colorPickerElement}
          style="top: {colorPickerPositionTop}px;"
        >
          <ColorPicker
            bind:rgb={colorPicked}
            isAlpha={false}
            isDialog={false}
            --cp-bg-color="#333"
            --cp-border-color="rgba(255, 255, 255, 0.6)"
            --cp-input-color="#555"
            --cp-button-hover-color="#777"
            --slider-width="30px"
          />
        </div>
      {/if}
      <div class="li__feature">
        <div class="li__feature__ele">
          <div class="li__feature__ele__head">
            <div class="li__feature__ele__head__code">
              {feature.element.code}
            </div>
            <div class="li__feature__ele__head__name">
              {feature.name.element}
              {#if feature.element.section === "country" && $CountryCodeMap}
                {@const code = feature.element.code}
                {@const flagCode = $CountryCodeMap[code].toLowerCase()}
                <img
                  src={`https://flagcdn.com/w40/${flagCode}.png`}
                  alt={feature.name.element}
                  width="30px"
                />
              {/if}
            </div>
          </div>
          <button class="li__feature__ele__del" on:click={() => del(feature)}>
            <MinusIcon size={1.2} />
          </button>
        </div>
        <div class="li__feature__fac">
          <div class="li__feature__fac__head">
            <div class="li__feature__fac__head__section">
              {feature.name.factor_section}
            </div>
            <div class="li__feature__fac__head__name">
              {feature.name.factor}
            </div>
          </div>
          <button
            class="li__feature__fac__download"
            on:click={() => download(feature)}
          >
            <DownloadIcon width={21} height={21} />
          </button>
        </div>
      </div>
    </div>
  {:else}
    <div class="empty">{$Text.GroupFeaturesEmpty}</div>
  {/each}
</main>

{#if downloadWidget}
  <Download
    elementSection={downloadTarget.elementSection}
    elementCode={downloadTarget.elementCode}
    factorSection={downloadTarget.factorSection}
    factorCode={downloadTarget.factorCode}
    on:close={() => (downloadWidget = false)}
  />
{/if}

<style>
  .loader {
    position: fixed;
    z-index: 11;
    top: 0;
    left: 0;
    width: 100vw;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: rgba(0, 0, 0, 0.4);
  }
  main {
    margin: 1rem;
    margin-right: 0.5rem;
    overflow: auto;
  }
  .empty {
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--white);
    opacity: 0.7;
  }
  .li {
    display: flex;
    align-items: center;
    position: relative;
  }
  .li__colorpicker {
    position: absolute;
    z-index: 10;
    left: -0.2rem;
  }
  .li__colorbox,
  .li__colorbox__edit-icon {
    width: 4rem;
    height: 4rem;
    border-radius: 0.5rem;
  }
  .li__colorbox {
    margin: 0 0.5rem;
    box-shadow: 0 0 0.7rem 0 rgba(0, 0, 0, 0.6);
    border: thin solid white;
  }
  .li__colorbox:hover {
    cursor: pointer;
  }
  .li__colorbox__edit-icon {
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .li__feature {
    width: 37rem;
  }
  .li__feature__ele,
  .li__feature__ele__head {
    display: flex;
    align-items: center;
  }
  .li__feature__ele__head {
    width: 33.9rem;
  }
  .li__feature__ele__head__code {
    background-color: #41425e;
  }
  .li__feature__ele__head__name {
    color: var(--white);
    display: flex;
    align-items: center;
    text-align: start;
    padding: 0.2rem 0.4rem;
    border-radius: 0.15rem;
    background-color: #36446c;
    margin: 0.5rem 0;
  }
  .li__feature__ele__head__name img {
    margin-left: 0.5rem;
  }
  .li__feature__ele__del {
    width: 2.5rem;
    height: 2.5rem;
    border-radius: 0.15rem;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0.7;
  }
  .li__feature__ele__del:hover {
    background-color: rgba(255, 255, 255, 0.1);
    cursor: pointer;
    opacity: 1;
  }
  .li__feature__fac__download {
    width: 2.5rem;
    height: 2.5rem;
    border-radius: 0.15rem;
    display: flex;
    align-items: center;
    justify-content: center;
    fill: white;
    opacity: 0.7;
  }
  .li__feature__fac__download:hover {
    background-color: rgba(255, 255, 255, 0.1);
    cursor: pointer;
    opacity: 1;
  }
  .li__feature__fac,
  .li__feature__fac__head {
    display: flex;
    align-items: center;
  }
  .li__feature__fac__head {
    width: 33.9rem;
  }
  .li__feature__fac__head__section {
    background-color: #613a55;
  }
  .li__feature__fac__head__name {
    background-color: #40533e;
  }
  .li__feature__ele__head__code,
  .li__feature__fac__head__section,
  .li__feature__fac__head__name {
    margin: 0.5rem;
    padding: 0.2rem 0.4rem;
    border-radius: 0.15rem;
    color: var(--white);
  }
  .li__feature__fac__head__section,
  .li__feature__fac__head__name {
    margin-top: 0;
  }
  .li__feature__fac__head__name {
    margin-left: 0;
  }
  .border-none {
    border: none;
  }
  .hover-none:hover {
    cursor: default;
    border: thin solid white;
  }
</style>
