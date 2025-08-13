all: test_android

test_android:
	briefcase build android

android:
	briefcase dist android

debian:
	rm -r build/pesten/debian
	briefcase build linux debian

