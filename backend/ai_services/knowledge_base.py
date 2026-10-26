"""BookLeaf policy supplied with the assignment, grouped for selective prompting."""

SECTIONS = {
    'ROYALTY': ('Authors receive 80% of net profit; BookLeaf receives 20%. Net profit is MRP less printing cost, platform commission and shipping. Royalties are calculated quarterly; payouts normally occur within 45 days after quarter end. The minimum payout threshold is ₹1,000, and smaller balances roll over. Payouts use bank transfer. Do not infer eligibility or payment initiation from a balance alone.'),
    'ISBN': ('BookLeaf assigns a unique ISBN under its publisher imprint. Authors needing their own imprint must obtain an ISBN independently. ISBN discrepancies require production team escalation; do not claim escalation has already happened.'),
    'PRINTING': ('Normal print turnaround is 5–7 business days after order confirmation. Printing may be in-house in Delhi or with Repro India or Epitome Books. Verified quality defects qualify for a free reprint; photos may be needed. Do not confirm a defect before review.'),
    'DISTRIBUTION': ('Platforms include Amazon India, Flipkart, Amazon US, Amazon UK and BookLeaf Store. Listings typically appear 7–10 business days after publication is complete. Stock resync may resolve issues in 24–48 hours after it is actually initiated.'),
    'PRODUCTION': ('Workflow: Manuscript Received → optional Editing → Cover Design → Typesetting → Proofreading → ISBN Assignment → Printing → Distribution Setup → Published & Live. Cover approvals and proofreading revisions can delay progress.'),
    'GENERAL': ('BookLeaf is a self-publishing company in India and the US. Packages include Standard Free and Bestseller Breakthrough. Services include cover design, typesetting, ISBN assignment, printing, distribution and royalty management.'),
}
TONE = 'Reply empathetically and professionally. Acknowledge the exact concern, state only verified facts, suggest a concrete next step, and be concise. Policy timelines are indicative, never guaranteed.'
