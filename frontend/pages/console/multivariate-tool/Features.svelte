<script lang="ts">
  import ColorPicker from "svelte-awesome-color-picker";
  import { api } from "../../../modules/request";
  import {
    FeatureGroups,
    FeatureGroupSelected,
    CountryCodeMap,
  } from "../../../modules/state";
  import EditIcon from "../../../assets/icon/EditIcon.svelte";
  import type { FeatureType } from "../../../modules/state";

  let main: HTMLElement;
  let colorHovered: FeatureType | null = null;
  let colorPickerOn: FeatureType | null = null;
  let colorPicked: { r: number; g: number; b: number; a: number } | null = null;
  let colorPickerPositionTop: number = 96;

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
    // 색 변경이 실시간으로 모든 상태 변수에 반영되기 때문에 변경 전, 후를 비교할 수가 없음
    // 항상 API 요청을 보내서 매번 마지막 상태를 서버에 반영하는 수밖에 없음
    await api.member.patch("/feature/group/feature", request);
  };

  const onColorPicker = (feature: FeatureType) => {
    const index = $FeatureGroupSelected.features.findIndex(
      (f) => f === feature
    ); // overflow를 처리하기 위해 해당 DOM 높이를 기반으로 위젯의 위치를 계산해야 함
    const liElement = main.getElementsByClassName("li")[index];
    colorPickerPositionTop = liElement.clientHeight + 9; // 9가 가장 적절함
    colorPickerOn = feature;
    colorPicked = colorEncode(feature.color);
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
</script>

<main bind:this={main}>
  {#each $FeatureGroupSelected.features as feature}
    <div class="li">
      <button
        class="li__colorbox"
        style="background-color: {feature.color};"
        class:border-none={colorHovered === feature}
        class:hover-none={colorPickerOn}
        on:click={() => onColorPicker(feature)}
        on:mouseenter={() => (colorHovered = feature)}
        on:mouseleave={() => (colorHovered = null)}
      >
        {#if colorHovered === feature && !colorPickerOn}
          <div class="li__colorbox__edit-icon"><EditIcon /></div>
        {/if}
      </button>
      {#if colorPickerOn === feature}
        <div
          class="li__colorpicker"
          use:clickOutside={colorUpdate}
          style="top: {colorPickerPositionTop}px;"
        >
          <ColorPicker
            bind:rgb={colorPicked}
            isAlpha={false}
            isDialog={false}
          />
        </div>
      {/if}
      <div class="li__feature">
        <div class="li__feature__ele">
          <div class="li__feature__ele__code">
            {feature.element.code}
          </div>
          <div class="li__feature__ele__name">
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
        <div class="li__feature__fac">
          <div class="li__feature__fac__section">
            {feature.name.factor_section}
          </div>
          <div class="li__feature__fac__name">
            {feature.name.factor}
          </div>
        </div>
      </div>
    </div>
  {:else}
    피쳐가 하나도 안들어 있어..
  {/each}
</main>

<style>
  .li {
    display: flex;
    align-items: center;
    padding-left: 0.5rem;
    position: relative;
  }
  .li__colorpicker {
    position: absolute;
    z-index: 10;
    left: 0.3rem;
    --cp-bg-color: #333;
    --cp-border-color: rgba(255, 255, 255, 0.6);
    --cp-input-color: #555;
    --cp-button-hover-color: #777;
  }
  .li__colorbox,
  .li__colorbox__edit-icon {
    width: 4rem;
    height: 4rem;
    border-radius: 0.5rem;
  }
  .li__colorbox {
    margin: 0 0.5rem;
    box-shadow: 0 0 2rem 0.1rem black;
    border: thin solid white;
  }
  .li__colorbox:hover {
    cursor: pointer;
  }
  .li__colorbox:first-of-type {
    margin-top: 1rem;
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
  .li__feature__ele {
    display: flex;
    align-items: center;
  }
  .li__feature__ele__code {
    background-color: #41425e;
  }
  .li__feature__ele__name {
    color: var(--white);
    display: flex;
    align-items: center;
    text-align: start;
  }
  .li__feature__ele__name img {
    margin-left: 0.5rem;
  }
  .li__feature__fac {
    display: flex;
    align-items: center;
  }
  .li__feature__fac__section {
    background-color: #613a55;
  }
  .li__feature__fac__name {
    background-color: #40533e;
  }
  .li__feature__ele__code,
  .li__feature__fac__section,
  .li__feature__fac__name {
    margin: 0.5rem;
    padding: 0.2rem 0.4rem;
    border-radius: 0.15rem;
    color: var(--white);
  }
  .li__feature__fac__section,
  .li__feature__fac__name {
    margin-top: 0;
  }
  .li__feature__fac__name {
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
