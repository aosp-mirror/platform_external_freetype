# TEEUI build rules

This directory holds build rules for building a minimal freetype library
for teeui. Teeui (Android system/teeui) provides minimal layout and
UI rendering facilities for restricted runtime environments. It is used
by the confirmationui trusted app for Trusty.

## rules.mk

This defines a freetype module for Trusty.

## rules.json

This is a generic json representation of the files and include paths
required to build the teeui freetype library. Sufficiently generic
build systems may be able to include this file directly, or it can be
used to generate build rules for other build systems.
