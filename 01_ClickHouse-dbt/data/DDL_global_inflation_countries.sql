CREATE TABLE global_inflation_countries (
    country_code String,
    country_name String,
    region String,
    sub_region String,
    intermediate_region String,
    indicator_code String,
    indicator_name String,
    year UInt16,
    inflation_rate Float64
) ENGINE = MergeTree() ORDER BY (country_code, year);