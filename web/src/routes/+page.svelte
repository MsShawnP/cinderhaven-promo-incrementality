<script>
	// The ROI Scorecard — the verdict. First paint must read in 30 seconds:
	// verdict line, one chart, three numbers (PLAN.md). Every figure is Method 0,
	// the naive pre-period-average baseline, and is labelled as such on screen.
	//
	// Imported at build time. The Python pipeline writes this file; a missing file
	// fails the build loudly rather than shipping stale numbers (build contract).
	import scorecard from '$lib/data/scorecard.json';

	const { portfolio, events } = scorecard;

	const usd = new Intl.NumberFormat('en-US', {
		style: 'currency',
		currency: 'USD',
		maximumFractionDigits: 0
	});
	const dollars = (cents) => usd.format(cents / 100);

	// Distribution for the header chart: the 129 estimable events grouped by
	// return on trade spend. This is a display grouping of the artifact's own
	// per-event roi / lost_money — not a new portfolio figure (those all come
	// from the pipeline, DECISIONS.md).
	const estimable = events.filter((e) => e.estimable);
	const made = estimable.filter((e) => !e.lost_money);
	const inRange = (e, lo, hi) => e.roi !== null && e.roi >= lo && e.roi < hi;

	const tiers = [
		{
			label: 'Lost money',
			hint: 'below break-even',
			n: estimable.filter((e) => e.lost_money).length,
			color: 'var(--ll-tokyo-40)'
		},
		{ label: 'Returned 1–2×', hint: '', n: made.filter((e) => inRange(e, 1, 2)).length, color: 'var(--ll-hk-70)' },
		{ label: 'Returned 2–4×', hint: '', n: made.filter((e) => inRange(e, 2, 4)).length, color: 'var(--ll-hk-55)' },
		{
			label: 'Returned 4×+',
			hint: '',
			// roi >= 4, plus the one zero-cost winner (roi null but made money).
			n: made.filter((e) => e.roi === null || e.roi >= 4).length,
			color: 'var(--ll-hk-20)'
		}
	];
	const maxTier = Math.max(...tiers.map((t) => t.n));

	const roiText = `${portfolio.portfolio_roi.toFixed(2)}×`;
	const lostPct = Math.round((portfolio.n_lost_money / portfolio.n_estimable) * 100);
</script>

<div class="lailara-container">
	<section class="scorecard">
		<p class="eyebrow">ROI Scorecard · Method 0</p>

		<h1 class="verdict">{portfolio.n_lost_money} of {portfolio.n_estimable} promotions lost money.</h1>

		<p class="lede ll-measure">
			Method 0 — the naive pre-period baseline, the most optimistic read there is —
			still puts {lostPct}% of estimable events below break-even. The portfolio clears
			{roiText} on the dollar only because a thin tail of winners carries a middle that
			mostly didn't pay back.
		</p>

		<!-- Three numbers: the CFO header (spend, net incremental margin, ROI),
		     all computed in the pipeline. -->
		<dl class="stats">
			<div class="stat">
				<dt>Trade spend</dt>
				<dd>{dollars(portfolio.total_accrued_spend_cents)}</dd>
				<p class="stat-note">accrued, {portfolio.n_estimable} estimable events</p>
			</div>
			<div class="stat">
				<dt>Net incremental margin</dt>
				<dd>{dollars(portfolio.net_incremental_margin_cents)}</dd>
				<p class="stat-note">manufacturer margin on incremental units</p>
			</div>
			<div class="stat stat--verdict">
				<dt>Portfolio ROI</dt>
				<dd>{roiText}</dd>
				<p class="stat-note">margin returned per dollar of spend</p>
			</div>
		</dl>

		<!-- One chart: where the estimable promotions landed. DOM bars, not raster —
		     vector-crisp for print and natively responsive to 375px. -->
		<figure class="chart">
			<figcaption>
				<h2>Where the {portfolio.n_estimable} estimable promotions landed</h2>
				<p class="chart-sub">Grouped by return on trade spend · Method 0 estimate</p>
			</figcaption>

			<div class="bars">
				{#each tiers as tier (tier.label)}
					<div class="bar-row">
						<span class="bar-label">{tier.label}</span>
						<div class="bar-track">
							<div
								class="bar-fill"
								style="width: {(tier.n / maxTier) * 100}%; background: {tier.color};"
							></div>
							<span class="bar-value">{tier.n}</span>
						</div>
					</div>
				{/each}
			</div>

			<p class="footnote">
				{portfolio.n_events - portfolio.n_estimable} of {portfolio.n_events} events not estimable
				by Method 0 (insufficient pre-period history), shown unranked below and excluded from
				these totals. Method 0 is the naive pre-period-average baseline — the first of several,
				shown before comparable-store methods. Synthetic data.
			</p>
		</figure>
	</section>
</div>

<style>
	.scorecard {
		font-family: var(--ll-sans);
		color: var(--ll-london-20);
	}

	.eyebrow {
		font-family: var(--ll-sans);
		font-size: 13px;
		font-weight: 600;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		color: var(--ll-red-42);
		margin: 0 0 var(--ll-space-md);
	}

	.verdict {
		font-family: var(--ll-serif);
		font-weight: 700;
		font-size: clamp(2rem, 6vw, 3.5rem);
		line-height: 1.05;
		letter-spacing: -0.02em;
		color: var(--ll-london-5);
		margin: 0 0 var(--ll-space-base);
		max-width: 15em;
	}

	.lede {
		font-size: 17px;
		line-height: 1.6;
		color: var(--ll-london-20);
		margin: 0 0 var(--ll-space-2xl);
	}

	/* Three numbers */
	.stats {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: var(--ll-space-lg);
		margin: 0 0 var(--ll-space-3xl);
		padding: var(--ll-space-lg) 0;
		border-top: 1px solid var(--ll-london-85);
		border-bottom: 1px solid var(--ll-london-85);
	}
	.stat {
		margin: 0;
	}
	.stat dt {
		font-size: 13px;
		font-weight: 600;
		letter-spacing: 0.03em;
		text-transform: uppercase;
		color: var(--ll-london-35);
		margin: 0 0 var(--ll-space-xs);
	}
	.stat dd {
		font-family: var(--ll-serif);
		font-weight: 700;
		font-size: clamp(1.75rem, 4vw, 2.25rem);
		letter-spacing: -0.02em;
		color: var(--ll-london-5);
		margin: 0;
		font-variant-numeric: tabular-nums;
		line-height: 1.1;
	}
	.stat--verdict dd {
		color: var(--ll-hk-25);
	}
	.stat-note {
		font-size: 13px;
		color: var(--ll-london-35);
		margin: var(--ll-space-xs) 0 0;
		line-height: 1.4;
	}

	/* One chart — DOM bars */
	.chart {
		margin: 0;
	}
	.chart figcaption h2 {
		font-family: var(--ll-serif);
		font-weight: 700;
		font-size: clamp(1.25rem, 3vw, 1.375rem);
		color: var(--ll-london-5);
		margin: 0 0 var(--ll-space-xxs);
	}
	.chart-sub {
		font-size: 14px;
		color: var(--ll-london-35);
		margin: 0 0 var(--ll-space-lg);
	}
	.bars {
		display: flex;
		flex-direction: column;
		gap: var(--ll-space-md);
	}
	.bar-row {
		display: grid;
		grid-template-columns: 8.5rem 1fr;
		align-items: center;
		gap: var(--ll-space-base);
	}
	.bar-label {
		font-size: 14px;
		color: var(--ll-london-20);
		text-align: right;
	}
	.bar-track {
		display: flex;
		align-items: center;
		gap: var(--ll-space-sm);
	}
	.bar-fill {
		height: 1.5rem;
		border-radius: var(--ll-radius);
		min-width: 2px;
	}
	.bar-value {
		font-family: var(--ll-serif);
		font-weight: 700;
		font-size: 18px;
		color: var(--ll-london-5);
		font-variant-numeric: tabular-nums;
	}
	.footnote {
		font-size: 12px;
		font-style: italic;
		line-height: 1.5;
		color: var(--ll-london-35);
		margin: var(--ll-space-lg) 0 0;
		max-width: var(--ll-body-max-width);
	}

	/* Phone-first: the header must fully work at 375px (DECISIONS.md). */
	@media (max-width: 640px) {
		.stats {
			grid-template-columns: 1fr;
			gap: var(--ll-space-base);
		}
		.bar-row {
			grid-template-columns: 1fr;
			gap: var(--ll-space-xxs);
		}
		.bar-label {
			text-align: left;
		}
	}
</style>
