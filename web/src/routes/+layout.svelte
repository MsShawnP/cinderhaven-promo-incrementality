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

		/* One shared right boundary for text. The display headline block and
		   every prose/footnote block wrap at the same edge, so a lede never
		   ends short of the H1 above it. Aliases the design-system body measure
		   (720px, lailara-frame.css) as a single source of truth. px not ch on
		   purpose: the frame forbids ch for measure (Source Sans's "0" glyph is
		   ~0.5em, so ch counts render ~half their nominal width). */
		:root {
			--content-measure: var(--ll-body-max-width);
		}
	</style>
</svelte:head>

<div class="lailara-page">
	<header class="lailara-header">
		<div class="lailara-nav-inner">
			<a class="lailara-wordmark" href="https://lailarallc.com">Lailara</a>
			<span class="lailara-tool-name">Lift Math</span>
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
			<p class="lailara-footer-cta">
				<a href="https://lailarallc.com/work/lift-math">Read the Lift Math case study →</a>
			</p>
			<p class="lailara-footer-note">
				Data is synthetic; methodology and deliverables are real.
			</p>
		</div>
	</footer>
</div>
