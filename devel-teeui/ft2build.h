/****************************************************************************
 *
 * ft2build.h
 *
 *   FreeType 2 build and setup macros (development version).
 *
 * Copyright (C) 1996-2019 by
 * David Turner, Robert Wilhelm, Werner Lemberg, and Google Inc.
 *
 * This file is part of the FreeType project, and may only be used,
 * modified, and distributed under the terms of the FreeType project
 * license, LICENSE.TXT.  By continuing to use, modify, or distribute
 * this file you indicate that you have read the license and
 * understand and accept it fully.
 *
 */

#pragma once

#define FT_CONFIG_OPTIONS_H  <ftoption.h>
#define FT_CONFIG_MODULES_H  <ftmodule.h>


/*
 * Undefine PROJECT defined by the LK build system, because it would clash with freetype's
 * definition in ttinterp.c.
 */
#undef PROJECT

#include <freetype/config/ftheader.h>
