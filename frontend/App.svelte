<script>
	// Echarts
	import * as echarts from "echarts";

	const host = window.location.origin;

	let chartBox;
	let searchText = "";

	async function getData(symbol) {
		const url = `${host}/api/data/time-series/symbol/adj-close?element=${symbol}`;
		const res = await fetch(url);
		return await res.json();
	}

	async function search() {
		console.log("요청 발신!");
		const data = await getData(searchText);
		const chart = echarts.init(chartBox);
		const option = {
			xAxis: {
				type: "category",
				data: data.t,
			},
			yAxis: {
				type: "value",
			},
			series: [
				{
					data: data.values,
					type: "line",
				},
			],
		};
		chart.setOption(option);
	}
</script>

<main>
	<input type="text" bind:value={searchText} />
	<button on:click={search}>Search</button>
	<div id="chart" bind:this={chartBox} style="width: 600px;height:400px;" />
</main>

<style>
	main {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: space-evenly;
	}
</style>
