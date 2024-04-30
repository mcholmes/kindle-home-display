# For building next-wakeup 
VERSION := v1.0.0-beta.4
SRC_FILES := $(shell find src -name '*.sh' -o -name '*.png')
NEXT_WAKEUP_SRC_FILES := $(shell find src/next-wakeup/src -name '*.rs')
TARGET_FILES := $(SRC_FILES:src/%=dist/%)

# Kindle scp params
# REMOTE_HSOT should correspond to your .ssh/config file
REMOTE_HOST := kindle
REMOTE_DIR := /mnt/us/dashboard

help:
	@echo "Usage: make <target>"
	@echo "Targets:"
	@awk '/^[a-zA-Z\-\_0-9]+:/ { \
			sub(":", "", $$1); \
			print "  " $$1 \
		}' Makefile

# dist: dist/next-wakeup dist/xh dist/local/state ${TARGET_FILES}
dist: dist/next-wakeup dist/local/state ${TARGET_FILES}

tarball: dist
	tar -C dist -cvzf kindle-dash-${VERSION}.tgz ./

dist/%: src/%
	@echo "Copying $<"
	@mkdir -p $(@D)
	@cp "$<" "$@"

# this used to be 'cross build' not 'cargo build'... but was hard to get running on a Mac
dist/next-wakeup: ${NEXT_WAKEUP_SRC_FILES}
	cd src/next-wakeup && cargo build --release --target armv7-unknown-linux-musleabi
	cp src/next-wakeup/target/armv7-unknown-linux-musleabi/release/next-wakeup dist/
	
dist/xh: tmp/xh
	cd tmp/xh && cross build --release --target arm-unknown-linux-musleabi
	docker run --rm \
		-v $(shell pwd)/tmp/xh:/src \
		rustembedded/cross:arm-unknown-linux-musleabi-0.2.1 \
		/usr/local/arm-linux-musleabi/bin/strip /src/target/arm-unknown-linux-musleabi/release/xh
	cp tmp/xh/target/arm-unknown-linux-musleabi/release/xh dist/

tmp/xh:
	mkdir -p tmp/
	git clone --depth 1 --branch v0.16.1 https://github.com/ducaale/xh.git tmp/xh

dist/local/state:
	mkdir -p dist/local/state

clean:
	rm -r dist/*

watch:
	watchexec -w src/ -p -- make

format:
	shfmt -i 4 -w -l src/**/*.sh

# For ease of interacting with device 
ssh:
	ssh $(REMOTE_HOST) -t "cd $(REMOTE_DIR) && sh"

# Kindle doesn't have rsync installed. Some jailbreaks/extensions include it.
# An armv7 binary is available here https://github.com/jbruechert/rsync-static
start:
	ssh $(REMOTE_HOST) -t "$(REMOTE_DIR)/start.sh"

stop:
	ssh $(REMOTE_HOST) -t "$(REMOTE_DIR)/stop.sh"

rsync:
	rsync -ri --rsync-path=$(REMOTE_DIR)/rsync-arm 	dist/* $(REMOTE_HOST):$(REMOTE_DIR)
	@echo ""
	rsync -ri --rsync-path=$(REMOTE_DIR)/rsync-arm 	KUAL/kindle-dash $(REMOTE_HOST):/mnt/us/extensions

push:
	scp -r dist/* $(REMOTE_HOST):$(REMOTE_DIR)
	scp -r KUAL/kindle-dash $(REMOTE_HOST):/mnt/us/extensions

print-logs:
	scp $(REMOTE_HOST):$(REMOTE_DIR)/logs/*.log /dev/stdout

copy-logs:
	scp $(REMOTE_HOST):$(REMOTE_DIR)/logs/*.log .

.PHONY: clean watch tarball format ssh start stop rsync push print-logs copy-logs