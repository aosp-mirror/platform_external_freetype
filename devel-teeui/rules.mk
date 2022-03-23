LOCAL_DIR := $(GET_LOCAL_DIR)

MODULE := $(LOCAL_DIR)

FREETYPE_ROOT := $(TRUSTY_TOP)/external/freetype

MODULE_SRCS += \
	$(FREETYPE_ROOT)/src/base/ftsystem.c \
	$(FREETYPE_ROOT)/src/base/ftinit.c \
	$(FREETYPE_ROOT)/src/base/ftdebug.c \
	$(FREETYPE_ROOT)/src/base/ftbase.c \
	$(FREETYPE_ROOT)/src/base/ftbbox.c \
	$(FREETYPE_ROOT)/src/base/ftglyph.c \
	$(FREETYPE_ROOT)/src/base/ftbitmap.c \
	$(FREETYPE_ROOT)/src/sfnt/sfnt.c \
	$(FREETYPE_ROOT)/src/truetype/truetype.c \
	$(FREETYPE_ROOT)/src/raster/raster.c \
	$(FREETYPE_ROOT)/src/smooth/smooth.c \
	$(FREETYPE_ROOT)/src/autofit/autofit.c \
	$(FREETYPE_ROOT)/src/gzip/ftgzip.c \

GLOBAL_INCLUDES += \
	$(LOCAL_DIR) \
	$(FREETYPE_ROOT)/include \

MODULE_COMPILEFLAGS := -U__ANDROID__ -DFT2_BUILD_LIBRARY
MODULE_COMPILEFLAGS += -Wno-implicit-fallthrough

MODULE_DEPS += \
	trusty/user/base/lib/libc-trusty \

include make/module.mk
