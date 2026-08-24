<script>
	// Walking-skeleton demo — the original pipeline proof, kept for reference after
	// the ROI Scorecard took over `/`. Observed-only facts, no estimator. See
	// src/incrementality/build_skeleton.py.
	import skeleton from '$lib/data/skeleton.json';

	const fmt = new Intl.NumberFormat('en-US');
</script>

<svelte:head>
	<title>Lift Math — build probe</title>
	<!-- Internal: the walking-skeleton artifact check, not a public view. -->
	<meta name="robots" content="noindex" />
</svelte:head>

<div class="lailara-container">
	<section class="skeleton">
		<p class="eyebrow">Walking skeleton — pipeline proof, not a deliverable</p>

		<h1>{fmt.format(skeleton.total_observed_units)}</h1>
		<p class="sub">total observed units across the promo-event scan series</p>

		<dl>
			<div>
				<dt>Promo events</dt>
				<dd>{fmt.format(skeleton.event_count)}</dd>
			</div>
			<div>
				<dt>Scan rows</dt>
				<dd>{fmt.format(skeleton.scan_row_count)}</dd>
			</div>
			<div>
				<dt>Data package</dt>
				<dd>cinderhaven-promo-response v{skeleton.package_version}</dd>
			</div>
		</dl>

		<p class="note ll-measure">
			Every number here is <strong>observed only</strong> — computed in Python from
			<code>pr.load()</code>, written as JSON, rendered by this static build. No estimator,
			no baseline, no truth. This page proved the pipe; the ROI Scorecard at
			<a href="/">/</a> is the deliverable.
		</p>
	</section>
</div>

<style>
	.skeleton {
		font-family: var(--ll-sans);
		color: var(--ll-london-20);
	}
	.eyebrow {
		font-size: 13px;
		font-weight: 600;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		color: var(--ll-london-35);
		margin: 0 0 var(--ll-space-lg);
	}
	h1 {
		font-family: var(--ll-serif);
		font-weight: 700;
		font-size: clamp(2.5rem, 8vw, 4rem);
		letter-spacing: -0.02em;
		color: var(--ll-london-5);
		margin: 0;
		line-height: 1;
		font-variant-numeric: tabular-nums;
	}
	.sub {
		margin: var(--ll-space-sm) 0 var(--ll-space-2xl);
		color: var(--ll-london-35);
	}
	dl {
		display: grid;
		gap: var(--ll-space-base);
		margin: 0 0 var(--ll-space-2xl);
		max-width: 32rem;
	}
	dl div {
		display: flex;
		justify-content: space-between;
		border-bottom: 1px solid var(--ll-london-85);
		padding-bottom: var(--ll-space-sm);
	}
	dt {
		color: var(--ll-london-35);
	}
	dd {
		margin: 0;
		font-variant-numeric: tabular-nums;
		color: var(--ll-london-5);
	}
	.note {
		font-size: 15px;
		line-height: 1.6;
		color: var(--ll-london-35);
	}
	code {
		font-size: 0.85em;
		background: var(--ll-london-95);
		padding: 0.1em 0.3em;
		border-radius: var(--ll-radius);
	}
	a {
		color: var(--ll-london-20);
		text-decoration: underline;
	}
	a:hover {
		color: var(--ll-chicago-20);
	}
</style>
