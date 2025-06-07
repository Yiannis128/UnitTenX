# Copyright 2025 Claudionor N. Coelho Jr

MODEL_NAME="openai"
IP = `python ../virtualbox.py ip`
TEST_REMOTE_EXECUTION = "coelho@$(IP)"
AGENT_REMOTE_VERSION = "10"
all:
	python ../virtualbox.py start FreeBSD
	make clean
	coverage erase
	AGENT_REMOTE_VERSION=$(AGENT_REMOTE_VERSION) \
	MODEL_NAME=$(MODEL_NAME) \
	TEST_REMOTE_EXECUTION=$(TEST_REMOTE_EXECUTION) \
	    coverage run -m pytest
	coverage report
	coverage html

ssh:
	ssh -v $(TEST_REMOTE_EXECUTION)

new_ip:
	ssh-keygen -R $(IP)
	ssh $(TEST_REMOTE_EXECUTION)

single:
	AGENT_REMOTE_VERSION=$(AGENT_REMOTE_VERSION) \
		MODEL_NAME=$(MODEL_NAME) \
		TEST_REMOTE_EXECUTION=$(TEST_REMOTE_EXECUTION) \
		coverage run -m pytest $(TEST_NAME)
	coverage report
	coverage html

clean:
	-@rm -rf ../utils/__pycache__ ../__pycache__ __pycache__
	-@rm -rf htmlcov .pytest_cache work/*
	-@rm -rf gold/__pycache__ gold/test_fact.py
