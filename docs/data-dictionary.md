# Data Dictionary

## customers

Customer profile records with `customer_id`, name, email, phone, status, created date, and region.

## accounts

Financial account records linked to customers through `customer_id`, including status, type, open date, and balance.

## transactions

Transaction activity linked to accounts and product reference codes, including amount, date, currency, and channel.

## product_reference

Reference data for valid product codes, product names, families, active flags, and risk tiers.

## employee_access

Governance events showing who accessed sensitive tables, at what access level, and whether the access was authorized.

## source_system_loads

Operational metadata describing recent source loads, load status, record counts, and freshness.

## data_lineage_events

Traceability events showing source tables, target tables, transformations, and event timestamps.
