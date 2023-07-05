<script>
	// Echarts
	// import * as echarts from "echarts";
	// let chartBox;
	// const chart = echarts.init(chartBox);
	// option = {
	// 	xAxis: {
	// 		type: "category",
	// 		data: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
	// 	},
	// 	yAxis: {
	// 		type: "value",
	// 	},
	// 	series: [
	// 		{
	// 			data: [150, 230, 224, 218, 135, 147, 260],
	// 			type: "line",
	// 		},
	// 	],
	// };
	// chart.setOption(option);

	let searchQuery = ""; // Input field에 입력될 값을 담을 변수

	const host = window.location.origin;
	function search() {
		console.log(searchQuery); // Search 버튼 클릭 시 input에 입력된 값을 출력
	}
</script>

<main>
	<input type="text" bind:value={searchQuery} />
	<button on:click={search}>Search</button>
	<!-- <div bind:this={chartBox} /> -->
</main>

<style>
	main {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: space-evenly;
	}
</style>
