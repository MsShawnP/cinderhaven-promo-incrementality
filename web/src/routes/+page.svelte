<script>
	// The ROI Scorecard — the verdict, now over two baseline methods with a toggle.
	// First paint still reads in 30 seconds: verdict line, one chart, three numbers.
	// Method 0 (naive pre-period) is shown first — the anti-rigging exhibit — and the
	// toggle reveals Method 1 (comparable-store), with the delta between them visible.
	//
	// Imported at build time. The Python pipeline writes this file; a missing file
	// fails the build loudly rather than shipping stale numbers (build contract).
	import scorecard from '$lib/data/scorecard.json';
	import { dollars, roiText, pct } from '$lib/format.js';

	const { portfolios, events } = scorecard;

	const METHOD_SHORT = { method0: 'Method 0', method1: 'Method 1' };
	const METHOD_TAG = {
		method0: 'Method 0 · pre-period',
		method1: 'Method 1 · comparable-store'
	};

	// Which method the header, chart and list reflect. Method 0 leads (naive, shown
	// first); the toggle switches to Method 1 and everything follows.
	let selected = $state('method0');
	const otherKey = $derived(selected === 'method0' ? 'method1' : 'method0');
	const active = $derived(portfolios[selected]);
	const other = $derived(portfolios[otherKey]);

	const ledeText = $derived(
		selected === 'method0'
			? 'Method 0 is the most forgiving measure available — each promotion judged against the eight weeks before it. Even so, half these events didn’t pay back. The portfolio clears ' +
					roiText(active.portfolio_roi) +
					' only because a thin tail of winners carries a middle that didn’t.'
			: 'Method 1 judges each promotion against comparable stores that didn’t run it — the stricter, concurrent test Method 0 is blind to. It clears ' +
					roiText(active.portfolio_roi) +
					' on the dollar. Toggle to Method 0 to see how much the naive pre-period read flatters the same promotions.'
	);

	// Distribution for the header chart: the estimable events grouped by return on
	// trade spend, for the active method. A display grouping of the artifact's own
	// per-event roi / lost_money — not a new portfolio figure (DECISIONS.md).
	function tiersFor(method) {
		const est = events.filter((e) => e[method].estimable);
		const made = est.filter((e) => !e[method].lost_money);
		const inRange = (e, lo, hi) => e[method].roi !== null && e[method].roi >= lo && e[method].roi < hi;
		return [
			{ label: 'Lost money', n: est.filter((e) => e[method].lost_money).length, color: 'var(--ll-tokyo-40)' },
			{ label: 'Returned 1–2×', n: made.filter((e) => inRange(e, 1, 2)).length, color: 'var(--ll-hk-70)' },
			{ label: 'Returned 2–4×', n: made.filter((e) => inRange(e, 2, 4)).length, color: 'var(--ll-hk-55)' },
			{
				label: 'Returned 4×+',
				// roi >= 4, plus any zero-cost winner (roi null but made money).
				n: made.filter((e) => e[method].roi === null || e[method].roi >= 4).length,
				color: 'var(--ll-hk-20)'
			}
		];
	}
	const tiers = $derived(tiersFor(selected));
	const maxTier = $derived(Math.max(...tiers.map((t) => t.n)));

	// Ranked event list, for the active method: estimable events by net margin; the
	// events this method cannot estimate are shown unranked below, never dropped
	// (spec 2.2, 3.5). Story labels mark the four seeded events; plan_status marks
	// phantom / unplanned. Marked, not claimed "found" — the Accuracy view's job.
	const STORY_LABELS = {
		pure_subsidy: 'Pure subsidy',
		hero_cannibal: 'Hero cannibal',
		pantry_trap: 'Pantry trap',
		clean_winner: 'Clean winner'
	};
	const ranked = $derived(
		events
			.filter((e) => e[selected].estimable)
			.slice()
			.sort((a, b) => b[selected].net_margin_cents - a[selected].net_margin_cents)
	);
	const unranked = $derived(events.filter((e) => !e[selected].estimable));

	// Table annotations, for the active method. Net-dip (spec 2.4): a giveaway share
	// > 1 means sales fell below the baseline during the promo — flagged, not a broken
	// percentage. Scan-funded phantoms accrue nothing, so their $0 spend and noisy
	// negative margin need a word (shared across methods).
	const isZeroPhantom = (e) => e.plan_status === 'phantom' && e.accrued_cost_cents === 0;
	const hasNetDip = $derived(ranked.some((e) => e[selected].baseline_exceeds_promoted));
	const hasZeroPhantom = $derived(ranked.some(isZeroPhantom));
</script>

<div class="lailara-container">
	<section class="scorecard">
		<p class="eyebrow">ROI Scorecard</p>

		<div class="toggle" role="tablist" aria-label="Baseline method">
			{#each ['method0', 'method1'] as key (key)}
				<button
					role="tab"
					aria-selected={selected === key}
					class="toggle-btn"
					class:active={selected === key}
					onclick={() => (selected = key)}
				>
					{METHOD_TAG[key]}
				</button>
			{/each}
		</div>

		<h1 class="verdict">{active.n_lost_money} of {active.n_estimable} promotions lost money.</h1>

		<p class="lede ll-measure">{ledeText}</p>

		<!-- Three numbers: the CFO header for the active method, each with the other
		     method's value beneath it so the delta is visible without toggling. -->
		<dl class="stats">
			<div class="stat">
				<dt>Trade spend</dt>
				<dd>{dollars(active.total_accrued_spend_cents)}</dd>
				<p class="stat-note">what these promotions actually cost, across the {active.n_estimable} estimable events</p>
				<p class="stat-delta">{METHOD_SHORT[otherKey]}: {dollars(other.total_accrued_spend_cents)}</p>
			</div>
			<div class="stat">
				<dt>Net incremental margin</dt>
				<dd>{dollars(active.net_incremental_margin_cents)}</dd>
				<p class="stat-note">manufacturer margin on incremental units</p>
				<p class="stat-delta">{METHOD_SHORT[otherKey]}: {dollars(other.net_incremental_margin_cents)}</p>
			</div>
			<div class="stat stat--verdict">
				<dt>Portfolio ROI</dt>
				<dd>{roiText(active.portfolio_roi)}</dd>
				<p class="stat-note">margin returned per dollar of spend</p>
				<p class="stat-delta">{METHOD_SHORT[otherKey]}: {roiText(other.portfolio_roi)}</p>
			</div>
		</dl>

		<!-- One chart: where the estimable promotions landed under the active method. -->
		<figure class="chart">
			<figcaption>
				<h2>Where the {active.n_estimable} estimable promotions landed</h2>
				<p class="chart-sub">Grouped by return on trade spend · {METHOD_TAG[selected]}</p>
			</figcaption>

			<div class="bars">
				{#each tiers as tier (tier.label)}
					<div class="bar-row">
						<span class="bar-label">{tier.label}</span>
						<div class="bar-track">
							<div class="bar-fill" style="width: {(tier.n / maxTier) * 100}%; background: {tier.color};"></div>
							<span class="bar-value">{tier.n}</span>
						</div>
					</div>
				{/each}
			</div>

			<p class="footnote">
				{active.n_events - active.n_estimable} of {active.n_events} events not estimable by
				{METHOD_SHORT[selected]}, shown unranked below and excluded from these totals. Method 0
				(naive pre-period) and Method 1 (comparable-store) are the two baselines on this site —
				toggle to compare. Treat them as floors, not the verdict.
			</p>
		</figure>

		<!-- The proof behind the numbers, one click deep — not the front door. -->
		<a class="accuracy-link" href="/accuracy">
			<span class="accuracy-link-lead">How wrong are these numbers?</span>
			<span class="accuracy-link-sub"
				>See both methods scored against known truth — the error, by regime, including where
				it is large. →</span
			>
		</a>

		<!-- Ranked event list for the active method, with the other method's ROI per
		     row so the method delta is visible event by event. -->
		<section class="ranked">
			<h2 class="ranked-title">Every promotion, ranked by net margin</h2>
			<p class="ranked-sub">
				{active.n_estimable} estimable events under {METHOD_SHORT[selected]}. Rows below
				break-even — margin under spend — are marked in the ROI column.
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
							<th class="col-num" scope="col">{METHOD_SHORT[otherKey]} ROI</th>
							<th class="col-num" scope="col">Giveaway</th>
						</tr>
					</thead>
					<tbody>
						{#each ranked as e, i (e.promo_id)}
							<tr class:lost={e[selected].lost_money}>
								<td class="col-rank">{i + 1}</td>
								<td class="col-promo">
									<span class="promo-head">
										<a class="promo-id" href="/event/{e.promo_id}">{e.promo_id}</a>
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
								<td class="col-num">{dollars(e[selected].net_margin_cents)}</td>
								<td class="col-num">{dollars(e.accrued_cost_cents)}</td>
								<td class="col-num roi" class:neg={e[selected].lost_money}
									>{roiText(e[selected].roi)}{#if e[selected].baseline_exceeds_promoted}<sup class="mark"
											>†</sup
										>{/if}</td
								>
								<td class="col-num other-roi">{roiText(e[otherKey].roi)}</td>
								<td class="col-num">{pct(e[selected].subsidized_cost_share)}</td>
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
							the baseline — a dip — so the baseline volume outweighs what actually sold.
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
					<h3>Not estimable by {METHOD_SHORT[selected]}</h3>
					<p class="unranked-note ll-measure">
						{unranked.length}
						{unranked.length === 1 ? 'event' : 'events'}
						{selected === 'method0'
							? 'with too little pre-period history for a naive baseline'
							: 'with too few comparable control stores for a trustworthy median'}. Excluded from
						the totals above and shown here — the denominator is never hidden. Some are estimable
						under {METHOD_SHORT[otherKey]}; toggle to see.
					</p>
					<ul>
						{#each unranked as e (e.promo_id)}
							<li>
								<a class="promo-id" href="/event/{e.promo_id}">{e.promo_id}</a>
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

	/* Method toggle */
	.toggle {
		display: inline-flex;
		border: 1px solid var(--ll-london-85);
		border-radius: var(--ll-radius);
		overflow: hidden;
		margin: 0 0 var(--ll-space-lg);
	}
	.toggle-btn {
		font-family: var(--ll-sans);
		font-size: 13px;
		font-weight: 600;
		padding: 8px 16px;
		border: none;
		background: transparent;
		color: var(--ll-london-35);
		cursor: pointer;
	}
	.toggle-btn + .toggle-btn {
		border-left: 1px solid var(--ll-london-85);
	}
	.toggle-btn:hover {
		background: var(--ll-london-95);
	}
	.toggle-btn.active {
		background: var(--ll-chicago-20);
		color: #fff;
	}
	.toggle-btn:focus-visible {
		outline: 2px solid var(--ll-london-5);
		outline-offset: -2px;
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
	.stat-delta {
		font-size: 13px;
		font-weight: 600;
		color: var(--ll-london-20);
		margin: var(--ll-space-xs) 0 0;
		font-variant-numeric: tabular-nums;
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

	/* Link into the accuracy view — the proof behind the numbers */
	.accuracy-link {
		display: block;
		margin: var(--ll-space-2xl) 0 0;
		padding: var(--ll-space-lg);
		border: 1px solid var(--ll-chicago-20);
		border-radius: var(--ll-radius);
		text-decoration: none;
		background: var(--ll-chicago-95);
	}
	.accuracy-link:hover {
		background: var(--ll-chicago-85);
	}
	.accuracy-link-lead {
		display: block;
		font-family: var(--ll-serif);
		font-weight: 700;
		font-size: clamp(1.125rem, 2.5vw, 1.25rem);
		color: var(--ll-chicago-20);
		margin: 0 0 var(--ll-space-xxs);
	}
	.accuracy-link-sub {
		display: block;
		font-size: 14px;
		line-height: 1.5;
		color: var(--ll-london-20);
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
	.other-roi {
		color: var(--ll-london-35);
	}
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
		text-decoration: none;
	}
	a.promo-id:hover {
		color: var(--ll-chicago-20);
		text-decoration: underline;
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
		.toggle {
			display: flex;
			width: 100%;
		}
		.toggle-btn {
			flex: 1;
		}
	}
</style>
