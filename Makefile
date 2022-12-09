.SUFFIXES:

.PHONY: all
all:
	@python3 main.py

.PHONY: build
build:
	@buildozer android debug

.PHONY: install
install:
	@adb install -r bin/*-debug.apk

.PHONY: debug
debug:
	@adb shell logcat | grep python

.PHONY: tar
tar:
	@cd .. && tar cvzf 2048.tgz\
	 2048/*.py\
	 2048/*.kv\
	 2048/*.spec\
	 2048/Makefile\
	 2048/data
