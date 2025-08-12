all: flatpak

android:
	rm -r build/pesten/android
	briefcase build android

debian:
	rm -r build/pesten/debian
	briefcase build linux debian

flatpak:
	rm -r build/pesten/linux/flatpak
	briefcase build linux flatpak
