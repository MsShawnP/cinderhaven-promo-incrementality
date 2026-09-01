// Display formatters shared by the Scorecard header and the ranked event list.
// Money arrives as integer cents from the pipeline; ratios as floats or null.

const usd = new Intl.NumberFormat('en-US', {
	style: 'currency',
	currency: 'USD',
	maximumFractionDigits: 0
});

/** Integer cents → "$12,345" (whole dollars; the header is not a ledger). */
export const dollars = (cents) => usd.format(cents / 100);

/** ROI ratio → "2.50×", or "—" when undefined (zero accrued cost). */
export const roiText = (roi) => (roi === null ? '—' : `${roi.toFixed(2)}×`);

/** Volume share (0–1+) → "62%", or "—" when undefined (no complied volume). */
export const pct = (share) => (share === null ? '—' : `${Math.round(share * 100)}%`);

/** Whole count → "5,735". The v0.6.1 event universe is five digits; commas keep the
 *  verdict and the headline readable. */
export const count = (n) => (n === null ? '—' : n.toLocaleString('en-US'));
