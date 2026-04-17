CREATE MATERIALIZED VIEW IF NOT EXISTS funding_by_ministry AS
SELECT ministry, funding_type, SUM(total_budget_allocated) as total_budget
FROM schemes_clean
GROUP BY ministry, funding_type;

CREATE MATERIALIZED VIEW IF NOT EXISTS sector_distribution AS
SELECT unnest(sector_eligibility) as sector, COUNT(*) as scheme_count, SUM(max_funding_amount) as total_funding
FROM schemes_clean
GROUP BY sector;

CREATE MATERIALIZED VIEW IF NOT EXISTS stage_coverage AS
SELECT unnest(startup_stage) as stage, COUNT(*) as scheme_count
FROM schemes_clean
GROUP BY stage;
