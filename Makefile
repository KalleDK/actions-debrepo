.PHONY: keys
keys:
	docker run --rm -i -t -v ${PWD}/keys:/keys debrepo create_gpg

.PHONY: img
img:
	docker build -t debrepo .

.PHONY: run
run:
	docker run --rm -i -t --env-file ${PWD}/.env -v ${PWD}/pkgs:/root/pkgs:ro -v ${PWD}/.build:/root/.build debrepo

.PHONY: debug
debug:
	docker run --rm -i -t --env-file ${PWD}/.env -v ${PWD}/pkgs:/root/pkgs:ro -v ${PWD}/.build:/root/.build debrepo /bin/bash