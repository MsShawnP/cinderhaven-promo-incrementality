<script>
	// Brand frame shared by every route. Classes come from the vendored
	// lailara-frame.css (web/static/lailara/); this file only composes them.
	let { children } = $props();
</script>

<svelte:head>
	<style>
		/* Warm canvas on the document itself, so overscroll and any gap outside
		   .lailara-page still reads as the brand canvas, never white. */
		html,
		body {
			margin: 0;
			background-color: #f5f3ee;
		}
	</style>
</svelte:head>

<div class="lailara-page">
	<header class="lailara-header">
		<div class="lailara-nav-inner">
			<a class="lailara-wordmark" href="https://lailarallc.com">Lailara</a>
			<span class="lailara-tool-name">Promo Incrementality</span>
		</div>
	</header>

	<main class="lailara-main">
		{@render children()}
	</main>

	<footer class="lailara-footer">
		<div class="lailara-footer-inner">
			<p>
				Built by <a href="https://lailarallc.com">Lailara LLC</a> — data hygiene and
				analytics consulting for specialty food brands scaling into national retail.
			</p>
			<p class="lailara-footer-note">
				Data is synthetic; methodology and deliverables are real.
			</p>
		</div>
	</footer>
</div>
