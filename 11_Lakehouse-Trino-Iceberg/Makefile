.EXPORT_ALL_VARIABLES:

DBT_TEST_USER_1=user1
DBT_TEST_USER_2=user2
DBT_TEST_USER_3=user3

start-trino:
	docker network create dbt-net || true
	./trino/init_trino.bash
