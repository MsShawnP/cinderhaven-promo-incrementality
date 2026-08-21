<script>
	// The ROI Scorecard — the verdict. First paint must read in 30 seconds:
	// verdict line, one chart, three numbers (PLAN.md). Every figure is Method 0,
	// the naive pre-period-average baseline, and is labelled as such on screen.
	//
	// Imported at build time. The Python pipeline writes this file; a missing file
	// fails the build loudly rather than shipping stale numbers (build contract).
	import scorecard from '$lib/data/scorecard.json';
	import { dollars, roiText, pct } from '$lib/format.js';

	const { portfolio, events } = scorecard;

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

	const portfolioRoi = roiText(portfolio.portfolio_roi);

	// Ranked event list. Estimable events ranked by net incremental margin
	// (defined for all of them); the two non-estimable events are shown unranked
	// at the bottom, never dropped — the denominator is never silently shrunk
	// (spec 2.2). Story labels mark the four seeded events; plan_status marks
	// phantom / unplanned. Seeded stories are marked, not claimed "found" — that
	// is the Accuracy view's job.
	const STORY_LABELS = {
		pure_subsidy: 'Pure subsidy',
		hero_cannibal: 'Hero cannibal',
		pantry_trap: 'Pantry trap',
		clean_winner: 'Clean winner'
	};
	const ranked = estimable
		.slice()
		.sort((a, b) => b.net_margin_cents - a.net_margin_cents);
	const unranked = events.filter((e) => !e.estimable);

	// Table annotations. Net-dip (spec 2.4): a giveaway share > 1 means sales
	// during the promo fell below the pre-period baseline, so it is not a broken
	// percentage — it is flagged. Scan-funded phantoms accrue nothing (no sale,
	// no scan), so their $0 spend and noisy negative margin need a word.
	const isZeroPhantom = (e) => e.plan_status === 'phantom' && e.accrued_cost_cents === 0;
	const hasNetDip = ranked.some((e) => e.baseline_exceeds_promoted);
	const hasZeroPhantom = ranked.some(isZeroPhantom);
</script>

<div class="lailara-container">
	<section class="scorecard">
		<p class="eyebrow">ROI Scorecard · Method 0</p>

		<h1 class="verdict">{portfolio.n_lost_money} of {portfolio.n_estimable} promotions lost money.</h1>

		<p class="lede ll-measure">
			Method 0 is the most forgiving measure available — each promotion judged against
			the eight weeks before it. Even so, half these events didn't pay back. The portfolio
			clears {portfolioRoi} only because a thin tail of winners carries a middle that didn't.
		</p>

		<!-- Three numbers: the CFO header (spend, net incremental margin, ROI),
		     all computed in the pipeline. -->
		<dl class="stats">
			<div class="stat">
				<dt>Trade spend</dt>
				<dd>{dollars(portfolio.total_accrued_spend_cents)}</dd>
				<p class="stat-note">
					what these promotions actually cost, across the {portfolio.n_estimable} estimable events
				</p>
			</div>
			<div class="stat">
				<dt>Net incremental margin</dt>
				<dd>{dollars(portfolio.net_incremental_margin_cents)}</dd>
				<p class="stat-note">manufacturer margin on incremental units</p>
			</div>
			<div class="stat stat--verdict">
				<dt>Portfolio ROI</dt>
				<dd>{portfolioRoi}</dd>
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
				these totals. Method 0 is the simplest baseline on this site — better ones follow. Treat
				it as the floor, not the verdict.
			</p>
		</figure>
	</section>

	<!-- Ranked event list: opt-in depth after the verdict. All 129 estimable
	     events by net margin, plus the 2 unranked non-estimable events. -->
	<section class="ranked">
		<h2 class="ranked-title">Every promotion, ranked by net margin</h2>
		<p class="ranked-sub">
			{portfolio.n_estimable} estimable events. Rows below break-even — margin under
			spend — are marked in the ROI column. Method 0 estimate.
		</p>

		<div class="lailara-table-wrap">
			<table class="event-table">
				<thead>
					<tr>
						<th class="col-rank" scope="col">#</th>
						<th class="col-promo" scope="col">Promotion</th>
						<th class="col-num" scope="col">Net margin</th>
						<th class="col-num" scope="col">Trade spend</th>
						<th class="col-num" scope="col">ROI</th>
						<th class="col-num" scope="col">Giveaway</th>
					</tr>
				</thead>
				<tbody>
					{#each ranked as e, i (e.promo_id)}
						<tr class:lost={e.lost_money}>
							<td class="col-rank">{i + 1}</td>
							<td class="col-promo">
								<span class="promo-head">
									<span class="promo-id">{e.promo_id}</span>
									{#if STORY_LABELS[e.story_tag]}
										<span class="badge badge-story">{STORY_LABELS[e.story_tag]}</span>
									{/if}
									{#if e.plan_status !== 'executed'}
										<span class="badge badge-status">{e.plan_status}</span>
									{/if}
									{#if isZeroPhantom(e)}<sup class="mark">‡</sup>{/if}
								</span>
								<span class="promo-meta"
									>{e.retailer_id.replace('RET-', '')} · {e.sku} · {e.promo_type}</span
								>
							</td>
							<td class="col-num">{dollars(e.net_margin_cents)}</td>
							<td class="col-num">{dollars(e.accrued_cost_cents)}</td>
							<td class="col-num roi" class:neg={e.lost_money}>{roiText(e.roi)}</td>
							<td class="col-num"
								>{pct(e.subsidized_cost_share)}{#if e.baseline_exceeds_promoted}<sup class="mark"
										>†</sup
									>{/if}</td
							>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>

		{#if hasNetDip || hasZeroPhantom}
			<ul class="table-notes ll-measure">
				{#if hasNetDip}
					<li>
						<span class="mark">†</span> Giveaway over 100%: sales during the promotion fell below
						the pre-period baseline — a dip — so the baseline volume outweighs what actually sold.
						Method 0 reads a dip and a weak promotion the same way.
					</li>
				{/if}
				{#if hasZeroPhantom}
					<li>
						<span class="mark">‡</span> Scan-funded phantom — the promotion never ran, so nothing
						accrued; the margin shown is estimation noise around zero.
					</li>
				{/if}
			</ul>
		{/if}

		{#if unranked.length}
			<div class="unranked">
				<h3>Not estimable by Method 0</h3>
				<p class="unranked-note ll-measure">
					{unranked.length} events with too little pre-period history for a naive baseline.
					Excluded from the totals above and shown here — the denominator is never hidden.
					A comparable-store baseline can estimate events like these; Method 0 can't.
				</p>
				<ul>
					{#each unranked as e (e.promo_id)}
						<li>
							<span class="promo-id">{e.promo_id}</span>
							<span class="promo-meta"
								>{e.retailer_id.replace('RET-', '')} · {e.sku} · {e.promo_type} ·
								{dollars(e.accrued_cost_cents)} spend</span
							>
						</li>
					{/each}
				</ul>
			</div>
		{/if}
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

	/* Ranked event list */
	.ranked {
		margin-top: var(--ll-space-3xl);
		padding-top: var(--ll-space-2xl);
		border-top: 1px solid var(--ll-london-85);
		font-family: var(--ll-sans);
	}
	.ranked-title {
		font-family: var(--ll-serif);
		font-weight: 700;
		font-size: clamp(1.25rem, 3vw, 1.375rem);
		color: var(--ll-london-5);
		margin: 0 0 var(--ll-space-xxs);
	}
	.ranked-sub {
		font-size: 14px;
		color: var(--ll-london-35);
		margin: 0 0 var(--ll-space-lg);
		max-width: var(--ll-body-max-width);
	}
	/* Wide table scrolls inside its own container at every width — the frame only
	   sets this below 640px, which would let the page scroll on tablet. */
	.lailara-table-wrap {
		overflow-x: auto;
		max-width: 100%;
		-webkit-overflow-scrolling: touch;
	}
	.event-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 14px;
	}
	.event-table thead th {
		font-size: 12px;
		font-weight: 600;
		letter-spacing: 0.03em;
		text-transform: uppercase;
		color: var(--ll-london-35);
		text-align: left;
		padding: 0 var(--ll-space-base) var(--ll-space-sm);
		border-bottom: 2px solid var(--ll-london-5);
		white-space: nowrap;
	}
	.event-table tbody td {
		padding: var(--ll-space-md) var(--ll-space-base);
		border-bottom: 1px solid var(--ll-london-85);
		vertical-align: baseline;
		color: var(--ll-london-20);
	}
	.col-num {
		text-align: right;
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
	}
	.col-rank {
		text-align: right;
		color: var(--ll-london-35);
		font-variant-numeric: tabular-nums;
		width: 2.5rem;
	}
	/* Lost-money rows: a 3px Tokyo rule on the leading edge — red as ink, not fill. */
	.event-table tbody td:first-child {
		border-left: 3px solid transparent;
	}
	.event-table tbody tr.lost td:first-child {
		border-left-color: var(--ll-tokyo-40);
	}
	.roi.neg {
		color: var(--ll-tokyo-40);
		font-weight: 600;
	}
	/* Footnote markers: dagger on net-dip giveaway cells, double-dagger on
	   scan-funded zero-cost phantoms. Explained in .table-notes below the table. */
	.mark {
		color: var(--ll-london-40);
		font-weight: 600;
	}
	sup.mark {
		font-size: 0.7em;
		padding-left: 1px;
	}
	.table-notes {
		list-style: none;
		padding: 0;
		margin: var(--ll-space-base) 0 0;
		display: grid;
		gap: var(--ll-space-xs);
		font-size: 12px;
		font-style: italic;
		line-height: 1.5;
		color: var(--ll-london-35);
	}
	.table-notes .mark {
		font-style: normal;
	}
	.promo-head {
		display: flex;
		align-items: center;
		gap: var(--ll-space-sm);
		flex-wrap: wrap;
	}
	.promo-id {
		font-weight: 600;
		color: var(--ll-london-5);
	}
	.promo-meta {
		display: block;
		font-size: 12px;
		color: var(--ll-london-35);
		margin-top: 2px;
	}
	.badge {
		font-size: 11px;
		font-weight: 500;
		letter-spacing: 0.02em;
		padding: 1px 6px;
		border-radius: var(--ll-radius);
		white-space: nowrap;
	}
	.badge-story {
		background: var(--ll-chicago-95);
		color: var(--ll-chicago-20);
	}
	.badge-status {
		background: var(--ll-sg-95);
		color: var(--ll-sg-35);
		text-transform: capitalize;
	}
	.unranked {
		margin-top: var(--ll-space-2xl);
	}
	.unranked h3 {
		font-family: var(--ll-serif);
		font-weight: 700;
		font-size: 18px;
		color: var(--ll-london-5);
		margin: 0 0 var(--ll-space-xs);
	}
	.unranked-note {
		font-size: 14px;
		line-height: 1.5;
		color: var(--ll-london-35);
		margin: 0 0 var(--ll-space-base);
	}
	.unranked ul {
		list-style: none;
		padding: 0;
		margin: 0;
		display: grid;
		gap: var(--ll-space-sm);
	}
	.unranked li {
		padding-left: var(--ll-space-md);
		border-left: 3px solid var(--ll-london-70);
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
