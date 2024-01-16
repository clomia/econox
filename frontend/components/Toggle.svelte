<script>
  export let value = false;
</script>

<div class="cntr">
  <div class="lbl" class:selected={value} />
</div>

<style>
  .lbl {
    position: relative;
    display: block;
    height: 22px;
    width: 40px;
    background: #000;
    border-radius: 100px;
    cursor: pointer;
    border: 2px solid #404040;
    transition: all 0.2s ease;
  }
  .lbl:after {
    position: absolute;
    left: -2px;
    top: -2px;
    display: block;
    width: 22px;
    height: 22px;
    border-radius: 100px;
    background: #a0a0a0;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.4);
    content: "";
    transition: all 0.3s ease;
  }
  .selected {
    background: #1db955;
    border-color: #1db955;
  }
  .selected:after {
    transform: translateX(18px);
    background: #fff;
  }
  .cntr {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
  }
</style>
