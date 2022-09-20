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
