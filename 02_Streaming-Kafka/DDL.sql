CREATE TABLE created_users (
        id UUID,
        first_name String,
        last_name String,
        gender String,
        address String,
        post_code String,
        email String,
        username String,
        registered_date String,
        phone String,
        picture String) ENGINE = MergeTree() ORDER BY (first_name, last_name);