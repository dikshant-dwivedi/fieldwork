SHELL := /bin/bash

.PHONY: doctor setup test demo verify clean topology explain listen send chat-alice chat-bob

doctor:
	@./scripts/host/doctor.sh

setup:
	@./scripts/host/vm.sh setup

test:
	@./scripts/host/vm.sh test

demo:
	@./scripts/host/vm.sh demo

verify:
	@./scripts/host/vm.sh verify

clean:
	@./scripts/host/vm.sh clean

topology:
	@./scripts/host/vm.sh topology

explain:
	@./scripts/host/explain.sh

listen:
	@./scripts/host/vm.sh listen

send:
	@./scripts/host/vm.sh send

chat-alice:
	@./scripts/host/vm.sh chat-alice

chat-bob:
	@./scripts/host/vm.sh chat-bob
