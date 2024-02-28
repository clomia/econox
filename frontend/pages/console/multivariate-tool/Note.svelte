<script lang="ts">
  import { api } from "../../../modules/request";
  import { FeatureGroupSelected, Text } from "../../../modules/state";
  import EditIcon from "../../../assets/icon/EditIcon.svelte";
  import Folder from "../../../assets/icon/Folder.svelte";
  import Check from "../../../assets/icon/Check.svelte";
  import CancelIcon from "../../../assets/icon/CancelIcon.svelte";
  import DownloadIcon from "../../../assets/icon/DownloadIcon.svelte";
  import Download from "./Download.svelte";

  let editOn = false;
  // editOn 상태에서 다른 그룹을 선택하는 경우를 처리하기 위함
  let beforeSelected = $FeatureGroupSelected;

  let textarea: HTMLTextAreaElement;
  $: if (textarea) {
    // 편집 버튼 누르면 자동으로 포커싱 해주기
    textarea.focus();
  }
  let textareaValue = $FeatureGroupSelected.description;
  const editStart = async () => {
    editOn = true;
    textareaValue = $FeatureGroupSelected.description;
  };
  const editConfirm = async () => {
    editOn = false;
    if (textareaValue === $FeatureGroupSelected.description) {
      return; // 변경사항이 없으면 API 요청 보내지 않기
    } else {
      $FeatureGroupSelected.description = textareaValue;
    }
    await api.member.patch("/feature/group", {
      group_id: $FeatureGroupSelected.id,
      description: textareaValue,
    });
  };
  const editCancel = () => {
    // Cancel이자 init이다. 포커싱이 바뀔때마다 실행해줘야 한다.
    textareaValue = $FeatureGroupSelected.description;
    editOn = false;
  };
  $: if (beforeSelected !== $FeatureGroupSelected) {
    editCancel();
    beforeSelected = $FeatureGroupSelected;
  }
  let downloadWidget = false;

  $: if (textareaValue?.length > 2000) {
    // 설명은 2000자를 초과할 수 없다.
    textareaValue = textareaValue.substring(0, 2000);
  }
</script>

<div class="header">
  <div class="header__group-name">
    <div class="header__group-name__icon"><Folder /></div>
    <div class="header__group-name__text">{$FeatureGroupSelected.name}</div>
  </div>
  <button class="header__download" on:click={() => (downloadWidget = true)}>
    <DownloadIcon width={23} height={23} />
  </button>
</div>

{#if downloadWidget}
  <Download on:close={() => (downloadWidget = false)} />
{/if}

<main>
  {#if editOn}
    <textarea
      style="resize: none;"
      bind:this={textarea}
      bind:value={textareaValue}
      placeholder={$Text.GroupNotePlaceholder}
    />
    <div class="btns">
      <button class="btns__cancel" on:click={editCancel}>
        <CancelIcon />
      </button>
      <button class="btns__confirm" on:click={editConfirm}><Check /></button>
    </div>
  {:else}
    {#if $FeatureGroupSelected.description}
      <pre class="content">{$FeatureGroupSelected.description}</pre>
    {:else}
      <div class="no-content">{$Text.GroupNoteNoneText}</div>
    {/if}
    <div class="btns">
      <button class="btns__edit" on:click={editStart}>
        <EditIcon />
      </button>
    </div>
  {/if}
</main>

<style>
  .header {
    display: flex;
    justify-content: space-between;
  }
  .header__group-name {
    font-size: 1.1rem;
    margin-top: 1rem;
    padding-left: 1.5rem;
    color: var(--white);
    display: flex;
    align-items: flex-start;
  }
  .header__group-name__icon {
    margin-right: 1rem;
  }
  .header__group-name__text {
    width: 36.5rem;
  }
  .header__download {
    width: 2.6rem;
    height: 2.6rem;
    fill: white;
    opacity: 0.7;
    margin-right: 0.5rem;
    margin-top: 0.5rem;
  }
  .header__download:hover {
    background-color: rgba(255, 255, 255, 0.2);
    cursor: pointer;
    opacity: 1;
  }
  main {
    display: flex;
    padding-bottom: 1rem;
    padding-left: 1.5rem;
    padding-top: 0.5rem;
  }
  textarea,
  .content,
  .no-content {
    height: 8rem;
    width: 41.3rem;
    color: var(--white);
    overflow: auto;
  }
  .content {
    white-space: pre-wrap;
    word-wrap: break-word;
  }
  .no-content {
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0.7;
    padding-bottom: 2rem;
  }
  .btns {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-end;
    margin-left: 0.3rem;
    margin-right: 0.5rem;
  }

  .btns__edit,
  .btns__cancel,
  .btns__confirm {
    height: 2.6rem;
    width: 2.6rem;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0.7;
  }

  .btns__edit:hover,
  .btns__cancel:hover,
  .btns__confirm:hover {
    background-color: rgba(255, 255, 255, 0.2);
    cursor: pointer;
    opacity: 1;
  }
</style>
